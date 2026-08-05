"""계열 후보 사전계산(rule: family-candidate-v1.0) — 후보는 판정이 아니다(ADR-011).

하나의 실질적 데이터가 여러 목록으로 분리 등록된 '계열'을 세 가지 결정론적
신호(제목 정규화·기관 내 동일 구조지문·가변 토큰 패턴)의 합집합으로 탐지한다.
대상은 FILE 목록만이다(API·STD는 구조·행수 신호가 없다). 자동 후보에는
오탐과 누락이 동시에 존재하므로 evidence_level과 review_status를 반드시
동반하며, 관측 스토어가 없으면 구조 신호 없이 CATALOG_ONLY로 강등된다.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

_PAREN = re.compile(r"[\(\[［（].*?[\)\]］）]")
_DIGIT = re.compile(r"[0-9０-９]+")
_SEP = re.compile(r"[\s_\-·.,~년월일차회호기'\"]+")
_TOKEN = re.compile(r"[_\s·\-]+")
_YEAR = re.compile(r"(19|20)\d{2}")

# 범용 스키마(연번·내용 등) 과대병합 방지 하한
_MIN_STRUCTURE_COLUMNS = 4


def _norm_title(title: str) -> str:
    t = _PAREN.sub(" ", title)
    t = _DIGIT.sub(" ", t)
    return _SEP.sub("", t)


def _load_structure_hashes(obs_path: Path) -> dict[str, set[str]]:
    """목록키 → 구조지문 집합. 컬럼 수 하한 미달 지문은 제외."""
    conn = sqlite3.connect(f"file:{obs_path}?mode=ro", uri=True)
    try:
        eligible = {
            h for h, c in conn.execute(
                "SELECT o.structure_hash, MAX(dt.column_count) FROM observations o "
                "JOIN data_tables dt ON dt.observation_id = o.observation_id "
                "GROUP BY o.structure_hash"
            ) if (c or 0) >= _MIN_STRUCTURE_COLUMNS
        }
        hashes: dict[str, set[str]] = defaultdict(set)
        for lk, h in conn.execute(
            "SELECT DISTINCT sa.list_key, o.structure_hash FROM source_assets sa "
            "JOIN observations o ON o.asset_id = sa.asset_id"
        ):
            if h in eligible:
                hashes[lk].add(h)
        return hashes
    finally:
        conn.close()


def _detect_clusters(records: list[dict], hashes: dict[str, set[str]]) -> dict[str, list[list[str]]]:
    """신호별 클러스터(record_id 목록). TITLE·STRUCTURE는 2건 이상, PATTERN은 3건 이상."""
    by_title: dict[tuple, list[str]] = defaultdict(list)
    by_hash: dict[tuple, list[str]] = defaultdict(list)
    by_pattern: dict[tuple, list[tuple[str, tuple]]] = defaultdict(list)

    for r in records:
        org = r["org_name"] or ""
        norm = _norm_title(r["title"] or "")
        if len(norm) >= 3:
            by_title[(org, norm)].append(r["record_id"])
        for h in hashes.get(r["list_key"], ()):
            by_hash[(org, h)].append(r["record_id"])
        tokens = [t for t in _TOKEN.split(r["title"] or "") if t]
        if len(tokens) >= 3 and len(tokens[-1]) >= 3:
            by_pattern[(org, tokens[0], tokens[-1], len(tokens))].append(
                (r["record_id"], tuple(tokens[1:-1]))
            )

    pattern_clusters = []
    for members in by_pattern.values():
        if len(members) < 3:
            continue
        middles = {m for _, m in members}
        if len(middles) >= max(3, int(0.8 * len(members))):  # 가운데가 실제로 가변일 때만
            pattern_clusters.append([rid for rid, _ in members])

    return {
        "TITLE": [v for v in by_title.values() if len(v) >= 2],
        "STRUCTURE": [v for v in by_hash.values() if len(v) >= 2],
        "PATTERN": pattern_clusters,
    }


def _relation_type(members: list[dict]) -> str:
    """자동 추정 관계 유형 — 검증 전 추정이며 판정이 아니다."""
    titles = [m["title"] or "" for m in members]
    n = len(titles)
    if sum(1 for t in titles if _YEAR.search(t)) >= 0.7 * n:
        return "TIME_LIKE"
    region_sets = []
    for m in members:
        try:
            regions = json.loads(m["regions"]) if isinstance(m["regions"], str) else (m["regions"] or [])
        except (TypeError, ValueError):
            regions = []
        # 지역 항목은 문자열·객체 혼재 가능 — 정렬 가능한 표현으로 통일
        region_sets.append(tuple(sorted(
            json.dumps(x, ensure_ascii=False, sort_keys=True) for x in regions
        )))
    non_empty = [s for s in region_sets if s]
    if len(non_empty) >= 0.7 * n and len(set(non_empty)) >= 0.7 * len(non_empty):
        return "REGION_LIKE"
    if sum(1 for t in titles if _DIGIT.search(t)) >= 0.7 * n:
        return "NUMBERED"
    return "NAME_PARTITION"


def _family_id(member_ids: list[str]) -> str:
    """구성원 집합에 결정론적으로 귀속되는 식별자. 구성이 바뀌면 id도 바뀐다
    — 검증 상태가 다른 구성의 계열로 잘못 승계되는 것을 막는다."""
    digest = hashlib.sha256("|".join(sorted(member_ids)).encode("utf-8")).hexdigest()
    return f"fam-{digest[:12]}"


def load_reviews(path: Path) -> dict[str, dict]:
    """사람 검증 결과(수동 관리 파일). family_id → {reviewStatus, note}."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("families", {})


def detect_families(
    conn: sqlite3.Connection,
    obs_path: Path | None = None,
    reviews: dict[str, dict] | None = None,
    detected_at: str = "",
) -> dict:
    """FILE 목록에서 계열 후보를 탐지해 families·family_members에 적재한다.

    반환: 요약 통계(빌드 리포트용).
    """
    reviews = reviews or {}
    conn.row_factory = sqlite3.Row
    records = [
        dict(r) for r in conn.execute(
            "SELECT record_id, list_key, org_name, title, regions FROM datasets WHERE list_type='FILE'"
        )
    ]
    by_id = {r["record_id"]: r for r in records}

    hashes: dict[str, set[str]] = {}
    structure_available = bool(obs_path and Path(obs_path).exists())
    if structure_available:
        hashes = _load_structure_hashes(Path(obs_path))

    clusters = _detect_clusters(records, hashes)

    # 합집합: union-find
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    signals_at_root: dict[str, set[str]] = defaultdict(set)
    for signal, cls in clusters.items():
        for members in cls:
            root = find(members[0])
            for rid in members[1:]:
                r2 = find(rid)
                if r2 != root:
                    parent[r2] = root
            signals_at_root[find(members[0])].add(signal)

    components: dict[str, list[str]] = defaultdict(list)
    signals_by_comp: dict[str, set[str]] = defaultdict(set)
    for rid in parent:
        components[find(rid)].append(rid)
    for root, sig in signals_at_root.items():
        signals_by_comp[find(root)].update(sig)

    inserted = 0
    counts = {"CATALOG_ONLY": 0, "PLUS_STRUCTURE": 0}
    review_counts: dict[str, int] = defaultdict(int)
    for root, member_ids in components.items():
        if len(member_ids) < 2:
            continue
        members = [by_id[r] for r in member_ids]
        fam_id = _family_id(member_ids)

        member_hashes = [hashes.get(m["list_key"], set()) for m in members]
        member_hashes = [h for h in member_hashes if h]
        plus = len(member_hashes) >= 2 and bool(set.intersection(*member_hashes))
        evidence = "PLUS_STRUCTURE" if plus else "CATALOG_ONLY"
        counts[evidence] += 1

        review = reviews.get(fam_id, {})
        review_status = review.get("reviewStatus", "UNREVIEWED")
        review_counts[review_status] += 1

        conn.execute(
            "INSERT INTO families (family_id, member_count, org_name, relation_type,"
            " evidence_level, signals, review_status, review_note, detection_rule, detected_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                fam_id, len(member_ids), members[0]["org_name"],
                _relation_type(members), evidence,
                json.dumps(sorted(signals_by_comp.get(root, set()))),
                review_status, review.get("note"),
                "family-candidate-v1.0", detected_at,
            ),
        )
        conn.executemany(
            "INSERT INTO family_members (family_id, record_id, list_key) VALUES (?, ?, ?)",
            [(fam_id, m["record_id"], m["list_key"]) for m in members],
        )
        inserted += 1

    return {
        "families": inserted,
        "memberRecords": conn.execute("SELECT COUNT(*) FROM family_members").fetchone()[0],
        "evidence": counts,
        "reviewStatus": dict(review_counts),
        "structureSignalAvailable": structure_available,
    }
