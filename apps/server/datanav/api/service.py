"""공용 쿼리 서비스 — MCP·REST가 같은 판정 로직을 사용한다(판단 로직 이중화 금지, §2)."""
from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import threading
from pathlib import Path

from ..config import (
    DEFAULT_PAGE_SIZE,
    MAX_COMPARE,
    MAX_PAGE_SIZE,
    MAX_QUERY_LENGTH,
    current_db_path,
    read_current_pointer,
)
from ..pipeline.completeness import compute_completeness, field_status
from ..pipeline.jsonld import catalog_record_jsonld, dataset_jsonld
from ..rules import (
    RULE_CARD,
    RULE_COMPLETENESS,
    RULE_DIFF,
    RULE_FAMILY,
    RULE_FRESHNESS,
    RULE_IDENTITY,
    RULE_RANKING,
    RULE_REGION,
)
from ..store.db import open_ro, row_to_record
from .envelope import decode_cursor, encode_cursor, envelope
from .errors import (
    DatasetNotFound,
    FilterNotAvailable,
    IndexNotReady,
    InvalidArgument,
    TooManyDatasets,
)

_FRESHNESS_DAYS = {
    "DAILY": 7, "WEEKLY": 30, "MONTHLY": 60,
    "QUARTERLY": 180, "SEMIANNUAL": 365, "ANNUAL": 540,
}

_VALID_LIST_TYPES = ("FILE", "API", "STD")
_STATS_AXES = ("theme", "org", "format", "completeness", "listType", "family")
_CHANGE_STATUSES = (
    "ADDED", "MODIFIED", "MISSING_FROM_SNAPSHOT", "REAPPEARED",
    "POSSIBLE_IDENTITY_CHANGE", "OFFICIALLY_WITHDRAWN",
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LIKE_ESCAPE = "\\"


def _matched_fields(rec: dict, tokens: list[str]) -> list[str]:
    """v1.6 additive: 검색어 토큰이 어느 목록 필드에 나타나는지 — '왜 이 결과인가'의 사실 표시.
    포함 판정 기준이라 FTS 완화(OR·접두) 일치와 다를 수 있다 — 빈 목록은 '필드 표시 불가'이지
    미일치 단정이 아니다."""
    kw = rec.get("keywords")
    checks = (
        ("title", rec.get("title")),
        ("keywords", " ".join(kw) if isinstance(kw, list) else (kw or "")),
        ("description", rec.get("description")),
        ("orgName", rec.get("org_name")),
    )
    return [name for name, text in checks
            if text and any(t in text.lower() for t in tokens)]


def _escape_like_literal(value: str) -> str:
    """SQLite LIKE pattern fragment for a literal user substring."""
    return (
        value
        .replace(_LIKE_ESCAPE, _LIKE_ESCAPE + _LIKE_ESCAPE)
        .replace("%", _LIKE_ESCAPE + "%")
        .replace("_", _LIKE_ESCAPE + "_")
    )


class Service:
    """읽기 전용 릴리스 DB 서비스.

    SQLite 연결은 스레드 간 공유하지 않는다 — 하나의 연결을 여러 스레드가 동시에
    사용하면 커서 상태가 오염된다(FastAPI 스레드풀에서 실측된 CPU 폭주 버그).
    스레드별 연결(threading.local)로 격리한다. 릴리스 DB는 불변이므로 안전하다.
    """

    def __init__(self, db_path: Path | None = None):
        try:
            path = db_path or current_db_path()
        except FileNotFoundError as e:
            raise IndexNotReady(str(e)) from None
        if not path.exists():
            raise IndexNotReady(f"카탈로그 DB가 없습니다: {path}")
        self._db_path = path
        self._local = threading.local()
        meta = {k: v for k, v in self.conn.execute("SELECT key, value FROM build_meta")}
        self.snapshot: str = meta.get("snapshot", "unknown")
        self.processed_at: str = meta.get("processedAt", "")
        self.release: str = meta.get("release", "")
        self._comp_dist_cache: dict | None = None  # 유형별 완전성 분포(지연 계산, 릴리스 불변)

    @property
    def conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = open_ro(self._db_path)
            self._local.conn = conn
        return conn

    # ------------------------------------------------------------ search
    def search_datasets(
        self,
        query: str | None = None,
        theme: str | None = None,
        org: str | None = None,
        fmt: str | None = None,
        update_cycle: str | None = None,
        license_code: str | None = None,
        list_type: str | None = None,
        region: str | None = None,
        include_inferred: bool = True,
        updated_after: str | None = None,
        cursor: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        interpret: bool = False,
        sort: str | None = None,
    ) -> dict:
        # v1.6 additive: 정렬 선택 — relevance(질의 필요)|modified. 기본은 기존 동작
        # (질의 있으면 관련도, 없으면 최신 수정순)이라 미지정 소비자는 불변.
        if sort and sort not in ("relevance", "modified"):
            raise InvalidArgument("sort는 relevance|modified", {"sort": sort})
        if query and len(query) > MAX_QUERY_LENGTH:
            raise InvalidArgument(f"query는 {MAX_QUERY_LENGTH}자 이하", {"length": len(query)})

        # 질의 해석(v1.5 additive, 옵트인): 검색어 토큰을 필터로 이관하고 근거를 노출한다.
        # 명시 필터가 이미 있는 축은 해석하지 않는다(명시 우선).
        interpreted_filters: list[dict] = []
        if interpret and query:
            from .plan import interpret_query
            explicit = {f for f, v in (("region", region), ("format", fmt),
                                       ("updateCycle", update_cycle), ("listType", list_type)) if v}
            remaining, interpreted_filters = interpret_query(query, skip_fields=explicit)
            for f in interpreted_filters:
                if f["field"] == "region":
                    region = f["value"]
                elif f["field"] == "format":
                    fmt = f["value"]
                elif f["field"] == "updateCycle":
                    update_cycle = f["value"]
                elif f["field"] == "listType":
                    list_type = f["value"]
            query = remaining or None
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise InvalidArgument(f"pageSize는 1~{MAX_PAGE_SIZE}", {"pageSize": page_size})
        if list_type and list_type.upper() not in _VALID_LIST_TYPES:
            raise FilterNotAvailable("listType은 FILE/API/STD", {"listType": list_type})
        if updated_after and not _DATE_RE.match(updated_after):
            raise InvalidArgument("updatedAfter는 YYYY-MM-DD 형식", {"updatedAfter": updated_after})

        offset = 0
        if cursor:
            offset = decode_cursor(cursor, self.snapshot).get("o", 0)

        where, params = [], []
        joins = ""
        warnings: list[str] = []

        if theme:
            where.append("(d.theme_top = ? OR d.theme_raw = ?)")
            params += [theme, theme]
        if org:
            where.append("d.org_name LIKE ?")
            params.append(f"%{org}%")
        if fmt:
            where.append(
                "EXISTS (SELECT 1 FROM json_each(d.formats) jf WHERE jf.value = ?)"
            )
            params.append(fmt.upper())
        if update_cycle:
            where.append("d.update_cycle = ?")
            params.append(update_cycle.upper())
        if license_code:
            where.append("d.license_code = ?")
            params.append(license_code.upper())
        if list_type:
            where.append("d.list_type = ?")
            params.append(list_type.upper())
        if updated_after:
            where.append("d.modified_date >= ?")
            params.append(updated_after)
        if region:
            cond = "json_extract(jr.value, '$.code') = ?"
            if not include_inferred:
                cond += " AND json_extract(jr.value, '$.evidence') = 'EXPLICIT_SPATIAL'"
            where.append(f"EXISTS (SELECT 1 FROM json_each(d.regions) jr WHERE {cond})")
            params.append(region)
            if include_inferred:
                warnings.append(
                    "region 매칭에 추론 근거(INFERRED_*)가 포함될 수 있습니다 — 각 결과의 regions.evidence를 확인하세요(rule: region-match-v1.0)."
                )

        fts_mode = None
        if query and query.strip():
            tokens = [t for t in re.split(r"\s+", query.strip()) if t]
            fts_expr = " ".join('"' + t.replace('"', '""') + '"' for t in tokens)
            joins = "JOIN datasets_fts f ON f.rowid = d.rowid"
            base_where = list(where)
            where.append("datasets_fts MATCH ?")
            params_fts = params + [fts_expr]
            order = "ORDER BY bm25(datasets_fts, 4.0, 3.0, 1.0, 2.0), d.record_id"
            fts_mode = "AND"
            total = self._count(joins, where, params_fts)
            if total == 0 and len(tokens) > 1:
                fts_expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in tokens)
                params_fts = params + [fts_expr]
                total = self._count(joins, where, params_fts)
                fts_mode = "OR-fallback"
                warnings.append("전체 단어 일치 결과가 없어 부분 일치(OR)로 완화해 검색했습니다.")
            params = params_fts
            score_col = "bm25(datasets_fts, 4.0, 3.0, 1.0, 2.0) AS score"
            if sort == "modified":  # 질의로 거르되 순서는 최신 수정(v1.6)
                order = "ORDER BY d.modified_date DESC, d.record_id"
                fts_mode = f"{fts_mode}/sort=modified"
        else:
            order = "ORDER BY d.modified_date DESC, d.record_id"
            score_col = "NULL AS score"
            total = self._count(joins, where, params)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        rows = self.conn.execute(
            f"SELECT d.*, {score_col} FROM datasets d {joins} {where_sql} {order} LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()

        q_tokens = [t.lower() for t in re.split(r"\s+", query.strip()) if t] if query and query.strip() else []
        items = []
        for i, r in enumerate(rows):
            rec = row_to_record(r)
            item = self._summary(rec)
            # v1.8 additive: 서버 정렬의 절대 순위 — score 부호 오독과 무관한 정본 순위
            item["rank"] = offset + i + 1
            if rec.get("score") is not None:
                item["score"] = round(rec["score"], 4)
            if q_tokens:
                item["matchedFields"] = _matched_fields(rec, q_tokens)
            items.append(item)

        has_more = offset + len(rows) < total
        data = {
            "items": items,
            "nextCursor": encode_cursor({"s": self.snapshot, "o": offset + len(rows)}) if has_more else None,
            "hasMore": has_more,
            "totalEstimate": total,
            "ranking": {
                "method": f"bm25(fts5)/{fts_mode}" if fts_mode else "modified_date desc",
                "version": RULE_RANKING,
                "indexVersion": self.release,
                "embeddingModel": None,
                "tieBreak": "record_id asc",
                # v1.5 additive: 정렬 방향을 사실로 노출(프론트의 문자열 패턴 추론 제거)
                "direction": "desc",
                "basis": "modified_date" if (not fts_mode or sort == "modified") else "relevance",
                # v1.8 additive: score 해석 방향 — SQLite FTS5 bm25()는 낮을수록 상위(음수).
                # sort=modified여도 score 값 자체의 의미는 동일하다(정렬 기준은 basis가 말한다).
                "scoreDirection": "LOWER_IS_MORE_RELEVANT" if fts_mode else "NOT_APPLICABLE",
            },
        }
        rules = [RULE_RANKING, RULE_REGION, RULE_IDENTITY]
        if interpret:
            data["interpretedFilters"] = interpreted_filters
            if interpreted_filters:
                from .plan import RULE_QUERY_INTERPRET
                rules.append(RULE_QUERY_INTERPRET)
        return envelope(data, self.snapshot, rules, warnings)

    def _count(self, joins: str, where: list[str], params: list) -> int:
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        return self.conn.execute(
            f"SELECT COUNT(*) FROM datasets d {joins} {where_sql}", params
        ).fetchone()[0]

    # ------------------------------------------------------------ get
    def get_dataset(self, record_id: str, view: str = "card") -> dict:
        if view not in ("card", "normalized", "source", "jsonld"):
            raise InvalidArgument("view는 card|normalized|source|jsonld", {"view": view})
        row = self.conn.execute(
            "SELECT * FROM datasets WHERE record_id = ?", (record_id,)
        ).fetchone()
        if row is None:
            # 목록키로 재시도(중복키 레코드 안내)
            alts = self.conn.execute(
                "SELECT record_id FROM datasets WHERE list_key = ?", (record_id,)
            ).fetchall()
            if alts:
                raise DatasetNotFound(
                    "해당 목록키는 복수 유형으로 등재되어 있습니다 — record_id를 지정하세요",
                    {"candidates": [a[0] for a in alts], "rule": RULE_IDENTITY},
                )
            raise DatasetNotFound(f"데이터셋을 찾을 수 없습니다: {record_id}", {"recordId": record_id})
        rec = row_to_record(row)

        if view == "card":
            data = self._card(rec)
            rules = [RULE_CARD, RULE_FRESHNESS, RULE_REGION, rec["completeness_rule"]]
        elif view == "normalized":
            data = {k: v for k, v in rec.items() if k != "source_json"}
            rules = list(RULE_COMPLETENESS.values()) + [RULE_REGION]
        elif view == "source":
            data = {
                "sourceFields": json.loads(rec["source_json"]),
                "sourceRowNo": rec["source_row_no"],
                "note": "공공데이터포털 목록개방현황 원본 필드·값 그대로입니다.",
            }
            rules = []
        else:  # jsonld (정본)
            data = dataset_jsonld(rec, self.snapshot)
            rules = [rec["completeness_rule"]]

        issues = self.conn.execute(
            "SELECT issue_type, field, confidence, review_status FROM issues WHERE record_id = ?",
            (record_id,),
        ).fetchall()
        warnings = [
            f"메타데이터 이슈 관찰 {len(issues)}건 존재(자동 탐지, 검수 전) — 원본 확인 필요"
        ] if issues else []
        # v1.8 additive: 계열 후보(ADR-011) — 후보는 판정이 아니다. 이 목록이
        # 전부인지(계열의 일부인지)를 호스트가 판단할 수 있게 근거와 함께 제공.
        family = self._family_candidate(record_id)
        if family:
            rules.append(RULE_FAMILY)
        return envelope(
            {"view": view, "dataset": data, "familyCandidate": family},
            self.snapshot, rules, warnings,
        )

    @property
    def families_available(self) -> bool:
        """이 릴리스에 계열 후보 테이블이 있는가 — 도입 전 빌드면 False(부재≠0건)."""
        if not hasattr(self, "_families_available"):
            self._families_available = bool(self.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='families'"
            ).fetchone())
        return self._families_available

    def _family_candidate(self, record_id: str) -> dict | None:
        if not self.families_available:
            return None
        fam = self.conn.execute(
            "SELECT f.* FROM families f JOIN family_members m ON m.family_id = f.family_id "
            "WHERE m.record_id = ?", (record_id,),
        ).fetchone()
        if fam is None:
            return None
        members = self.conn.execute(
            "SELECT m.record_id, d.title FROM family_members m "
            "JOIN datasets d ON d.record_id = m.record_id "
            "WHERE m.family_id = ? ORDER BY m.record_id LIMIT 10", (fam["family_id"],),
        ).fetchall()
        return {
            "familyId": fam["family_id"],
            "memberCount": fam["member_count"],
            "relationTypeAuto": fam["relation_type"],
            "evidenceLevel": fam["evidence_level"],
            "reviewStatus": fam["review_status"],
            "signals": json.loads(fam["signals"]),
            "members": [{"recordId": m["record_id"], "title": m["title"]} for m in members],
            "membersTruncated": fam["member_count"] > len(members),
            "rule": RULE_FAMILY,
            "note": "자동 탐지 후보입니다 — 확정된 계열이 아니며 오탐·누락이 있을 수 있습니다. "
                    "reviewStatus가 UNREVIEWED이면 사람 검증 전입니다.",
        }

    def get_catalog_record(self, record_id: str) -> dict:
        """CatalogRecord 정본 표현 — Dataset 정체성과 월별 목록 기술을 분리한다."""
        row = self.conn.execute(
            "SELECT * FROM datasets WHERE record_id = ?", (record_id,)
        ).fetchone()
        if row is None:
            raise DatasetNotFound(f"데이터셋을 찾을 수 없습니다: {record_id}", {"recordId": record_id})
        rec = row_to_record(row)
        return catalog_record_jsonld(rec, self.snapshot)

    # ---------------------------------------------- 데이터 구조 관측(S1b, v2.2 §8)
    @property
    def obs_conn(self):
        """관측 스토어 읽기 전용 연결(스레드별). 스토어 미배포면 None — 미수집과 동일 표면."""
        import os as _os
        if not hasattr(self._local, "obs_conn"):
            from ..observe.store import OBSERVATIONS_DB, open_ro as obs_open_ro
            p = Path(_os.environ.get("DATANAV_OBS_DB") or OBSERVATIONS_DB)
            self._local.obs_conn = obs_open_ro(p) if p.exists() else None
        return self._local.obs_conn

    def _structure_keys(self) -> set:
        """구조 확인 가능한 목록키 집합 — 검색 요약 structureAvailable용(릴리스 불변 캐시)."""
        if not hasattr(self, "_structure_keys_cache"):
            conn = self.obs_conn
            self._structure_keys_cache = (
                {r["list_key"] for r in conn.execute(
                    "SELECT DISTINCT list_key FROM record_coverage "
                    "WHERE coverage_status IN ('AVAILABLE', 'PARTIAL')")}
                if conn else set()
            )
        return self._structure_keys_cache

    def get_dataset_structure(self, record_id: str, view_examples: bool = True,
                              max_examples: int = 10) -> dict:
        """데이터 구조 관측 조회(계약 v1.2). 미수집·보류·차단은 오류가 아닌 정상 상태다.

        예시값 공개는 이중 게이트: 저장 시(안전·라이선스, S1a) + 응답 시
        DATANAV_EXAMPLES_PUBLIC(기본 0 — S0-2 법적 확인 전 보수 모드, v2.2 §12 S1c).
        """
        import os as _os
        max_examples = max(1, min(int(max_examples), 10))
        row = self.conn.execute(
            "SELECT record_id, list_key, list_type, list_url, row_count FROM datasets WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise DatasetNotFound(f"데이터셋을 찾을 수 없습니다: {record_id}", {"recordId": record_id})

        examples_public = _os.environ.get("DATANAV_EXAMPLES_PUBLIC", "0") == "1"
        base = {
            "recordId": row["record_id"],
            "listKey": row["list_key"],
            "distributionType": row["list_type"],
            "portalUrl": row["list_url"],
            "examplesPublic": examples_public,
        }
        if "row_count" in row.keys() and row["row_count"] is not None:
            base["rowCountListed"] = row["row_count"]
        rules = ["structure-status-v1.0"]
        warnings = []

        if row["list_type"] != "FILE":
            base["coverageStatus"] = "API_STRUCTURE_NOT_SUPPORTED_YET"
            base["reason"] = "API_STRUCTURE_NOT_SUPPORTED_YET"
            warnings.append("Open API 구조(오퍼레이션·파라미터·응답 필드)는 차기 단계에서 제공됩니다.")
            return envelope(base, self.snapshot, rules, warnings)

        oc = self.obs_conn
        cov = oc.execute(
            "SELECT coverage_status, available_asset_count, total_asset_count "
            "FROM record_coverage WHERE list_key = ? AND list_type = 'FILE'",
            (row["list_key"],),
        ).fetchone() if oc else None
        if cov is None:
            base["coverageStatus"] = "NOT_COLLECTED"
            base["reason"] = "NOT_COLLECTED"
            warnings.append("이 데이터의 구조는 아직 관측되지 않았습니다 — 품질 문제가 아니라 수집 순번입니다(§12).")
            return envelope(base, self.snapshot, rules, warnings)

        base["coverageStatus"] = cov["coverage_status"]
        base["coverage"] = {
            "availableAssets": cov["available_asset_count"],
            "totalAssets": cov["total_asset_count"],
        }
        base["evidenceLevel"] = "FILE_OBSERVATION"
        rules += ["column-type-observation-v1.0", "example-extraction-v1.0", "sample-safety-v1.0"]

        assets = oc.execute(
            "SELECT a.asset_id, a.file_name, a.container_name, a.format, a.shape, "
            "       c.status, c.failure_reason, c.current_observation_id "
            "FROM source_assets a JOIN asset_coverage c USING (asset_id) "
            "WHERE a.list_key = ? AND a.list_type = 'FILE' ORDER BY a.file_name",
            (row["list_key"],),
        ).fetchall()
        MAX_ASSETS = 20
        if len(assets) > MAX_ASSETS:
            warnings.append(f"자산이 {len(assets)}개라 처음 {MAX_ASSETS}개만 반환합니다 — 전체는 포털 원문에서 확인하세요.")
        base["assets"] = [self._structure_asset(oc, a, view_examples and examples_public,
                                                max_examples) for a in assets[:MAX_ASSETS]]

        if not examples_public:
            warnings.append("예시값은 발췌 제공 범위의 법적 확인(S0-2) 전까지 비공개입니다 — 컬럼명·관측 유형·건수만 제공합니다.")
        warnings.append("예시값·관측 유형은 관측 표본이며 전체 값의 분포·품질을 대표하지 않습니다. 원본 파일 해시가 제공되지 않은 관측은 UNVERIFIED_SOURCE로 표기됩니다.")
        return envelope(base, self.snapshot, rules, warnings)

    def _structure_asset(self, oc, a, show_examples: bool, max_examples: int) -> dict:
        out = {
            "fileName": a["file_name"],
            "containerName": a["container_name"],
            "format": a["format"],
            "shape": a["shape"],
            "status": a["status"],
            "failureReason": a["failure_reason"],
        }
        obs_id = a["current_observation_id"]
        if not obs_id:
            return out
        obs = oc.execute(
            "SELECT observed_at, provenance, scan_scope, scan_scope_assumed, license_gate "
            "FROM observations WHERE observation_id = ?", (obs_id,)).fetchone()
        out["observation"] = {
            "observationId": obs_id,
            "observedAt": obs["observed_at"],
            "provenance": obs["provenance"],
            "scanScope": obs["scan_scope"] + ("(ASSUMED)" if obs["scan_scope_assumed"] else ""),
            "licenseGate": obs["license_gate"],
        }
        tables = []
        for t in oc.execute(
                "SELECT table_id, sheet_name, source_path, table_index, scan_scope, "
                "       rows_scanned, row_count_total, column_count FROM data_tables "
                "WHERE observation_id = ? ORDER BY table_index", (obs_id,)):
            cols = []
            for c in oc.execute(
                    "SELECT ordinal, source_name, observed_type, distinct_count, "
                    "       distinct_approx, example_status, safety_status, examples, "
                    "       example_method, note FROM file_columns "
                    "WHERE table_id = ? ORDER BY ordinal", (t["table_id"],)):
                col = {
                    "ordinal": c["ordinal"],
                    "sourceName": c["source_name"],
                    "observedType": c["observed_type"],
                    "distinctCount": c["distinct_count"],
                    "distinctApprox": bool(c["distinct_approx"]),
                    "exampleStatus": c["example_status"],
                    "safetyStatus": c["safety_status"],
                    "exampleMethod": c["example_method"],
                    "note": c["note"],
                }
                if show_examples and c["examples"]:
                    col["examples"] = json.loads(c["examples"])[:max_examples]
                cols.append(col)
            tables.append({
                "sheetName": t["sheet_name"],
                "sourcePath": t["source_path"],
                "tableIndex": t["table_index"],
                "scanScope": t["scan_scope"],
                "rowsScanned": t["rows_scanned"],
                "rowCountObserved": t["row_count_total"],
                "columnCount": t["column_count"],
                "columns": cols,
            })
        out["tables"] = tables
        return out

    def search_by_columns(self, column_keywords: list[str], page_size: int = 20) -> dict:
        """원본 컬럼명 기준 검색(계약 v1.3, S2). 모든 키워드가 각각 어떤 컬럼명에
        부분 일치해야 한다(AND). 검색 대상은 구조가 관측된 레코드뿐이며 커버리지를
        응답에 명시한다 — '없음'과 '미수집'을 구분하기 위함(v2.2 §12)."""
        keywords = [k.strip() for k in (column_keywords or []) if k and k.strip()]
        if not keywords:
            raise InvalidArgument("columnKeywords가 비어 있습니다")
        if len(keywords) > 5:
            raise InvalidArgument("컬럼 키워드는 최대 5개", {"count": len(keywords)})
        if any(len(k) > 50 for k in keywords):
            raise InvalidArgument("컬럼 키워드는 각 50자 이하")
        page_size = max(1, min(int(page_size), 100))

        oc = self.obs_conn
        coverage = {
            "searchedRecords": len(self._structure_keys()),
            "fileRecordsTotal": self.conn.execute(
                "SELECT COUNT(*) FROM datasets WHERE list_type='FILE'").fetchone()[0],
        }
        matched: dict[str, dict[str, list[str]]] = {}
        if oc:
            per_kw = []
            for kw in keywords:
                pattern = f"%{_escape_like_literal(kw)}%"
                rows = oc.execute(
                    "SELECT list_key, source_name FROM record_column_index "
                    "WHERE source_name LIKE ? ESCAPE '\\'", (pattern,)).fetchall()
                m: dict[str, list[str]] = {}
                for r in rows:
                    m.setdefault(r["list_key"], []).append(r["source_name"])
                per_kw.append((kw, m))
            keys = set(per_kw[0][1])
            for _, m in per_kw[1:]:
                keys &= set(m)
            for lk in keys:
                matched[lk] = {kw: sorted(m[lk])[:5] for kw, m in per_kw}

        items = []
        for lk in sorted(matched)[:page_size]:
            row = self.conn.execute(
                "SELECT * FROM datasets WHERE list_key = ? AND list_type = 'FILE' LIMIT 1",
                (lk,)).fetchone()
            if row is None:
                continue  # 카탈로그 스냅샷과 관측의 시점 차 — 현재 목록에 없는 키는 제외
            item = self._summary(row_to_record(row))
            item["matchedColumns"] = [
                {"keyword": kw, "columns": cols} for kw, cols in matched[lk].items()
            ]
            items.append(item)

        warnings = [
            f"이 검색은 구조가 관측된 {coverage['searchedRecords']:,}건(FILE "
            f"{coverage['fileRecordsTotal']:,}건 중) 안에서만 수행되었습니다 — "
            "결과에 없다고 해당 컬럼이 없는 것이 아닙니다(미수집일 수 있음).",
            "일치 기준은 원본 컬럼명 부분 일치입니다 — 의미 동일성·결합 가능성은 확인되지 않았습니다.",
        ]
        data = {
            "columnKeywords": keywords,
            "items": items,
            "totalEstimate": len(matched),
            "hasMore": len(matched) > page_size,
            "coverage": coverage,
        }
        return envelope(data, self.snapshot,
                        ["structure-status-v1.0", RULE_IDENTITY], warnings)

    def _structure_columns_for(self, list_key: str) -> list[str] | None:
        oc = self.obs_conn
        if not oc or list_key not in self._structure_keys():
            return None
        return [r["source_name"] for r in oc.execute(
            "SELECT source_name FROM record_column_index WHERE list_key = ? "
            "ORDER BY source_name", (list_key,))]

    def _comp_dist(self) -> dict:
        """유형별 완전성 점수 분포 — 상대 위치(topPercent)·최빈값(typical) 판정용.
        릴리스 DB는 불변이므로 1회 계산해 캐시한다(경합해도 같은 값이라 무해)."""
        if self._comp_dist_cache is None:
            dist: dict = {}
            rows = self.conn.execute(
                "SELECT completeness_profile p, completeness_score s, COUNT(*) n "
                "FROM datasets GROUP BY p, s"
            ).fetchall()
            for r in rows:
                d = dist.setdefault(r["p"], {"total": 0, "mode": (None, 0), "scores": []})
                d["total"] += r["n"]
                d["scores"].append((r["s"], r["n"]))
                if r["n"] > d["mode"][1]:
                    d["mode"] = (r["s"], r["n"])
            self._comp_dist_cache = dist
        return self._comp_dist_cache

    def _completeness(self, rec: dict) -> dict:
        """완전성 표현 확장(v1.1.0, 하위 호환 필드 추가): 무엇이 비었는지(keyFields)와
        유형 내 상대 위치(topPercent·typical)를 동반한다 — 점수만으로는 89%가 동일 값(0.8125)이라
        변별·해석이 불가능하다는 관찰(§6)에 따른 표현 개선."""
        comp = compute_completeness(rec)
        comp["keyFields"] = {
            "spatial": bool(rec["spatial_raw"]),
            "temporal": bool(rec["temporal_raw"]),
            "dataLimits": bool(rec["data_limits"]),
        }
        d = self._comp_dist().get(comp["profile"])
        if d and d["total"]:
            higher = sum(n for s, n in d["scores"] if s > comp["score"])
            comp["topPercent"] = round(higher / d["total"] * 100, 1)
            comp["typical"] = comp["score"] == d["mode"][0]
            comp["typicalShare"] = round(d["mode"][1] / d["total"] * 100, 1)
        return comp

    def _summary(self, rec: dict) -> dict:
        s = {
            "recordId": rec["record_id"],
            "listKey": rec["list_key"],
            "listType": rec["list_type"],
            "title": rec["title"],
            "orgName": rec["org_name"],
            "theme": {"top": rec["theme_top"], "sub": rec["theme_sub"]},
            "formats": rec["formats"],
            "updateCycle": rec["update_cycle"],
            "modifiedDate": rec["modified_date"],
            "completeness": self._completeness(rec),
            "structureAvailable": rec["list_key"] in self._structure_keys(),
            "regions": rec["regions"],
            "portalUrl": rec["list_url"],
        }
        # v1.6 교정: 스펙(summaryItem.rowCountListed)에 있으나 미방출이던 필드 — 목록 기재 행수
        if rec.get("row_count") is not None:
            s["rowCountListed"] = rec["row_count"]
        return s

    def _card(self, rec: dict) -> dict:
        card = self._summary(rec)
        card["completeness"]["fields"] = field_status(rec)  # 점수의 분해 근거(체크리스트)
        card.update({
            "keywords": rec["keywords"],
            "description": rec["description"],
            "dataLimits": rec["data_limits"],
            "notes": rec["notes"],
            "license": {"code": rec["license_code"], "raw": rec["license_raw"]},
            "updateCycleRaw": rec["update_cycle_raw"],
            "createdDate": rec["created_date"],
            "rowCount": rec["row_count"],
            "apiType": rec["api_type"],
            "fee": rec["fee"],
            "spatial": rec["spatial_raw"],
            "temporal": rec["temporal_raw"],
            "isNationalCore": bool(rec["is_national_core"]),
            "isStandard": bool(rec["is_standard"]),
            "freshness": self._freshness(rec),
            "evidenceLevel": "CATALOG_METADATA_ONLY",
            "cardRule": RULE_CARD,
            "portal": {
                "listKey": rec["list_key"],
                "orgName": rec["org_name"],
                "listUrl": rec["list_url"],
                "listBaseDate": self.snapshot,
                "analyzedAt": self.processed_at,
            },
        })
        return card

    def _freshness(self, rec: dict) -> dict:
        cycle = rec["update_cycle"]
        days = _FRESHNESS_DAYS.get(cycle)
        if days is None or not rec["modified_date"]:
            return {"status": "UNKNOWN", "rule": RULE_FRESHNESS}
        try:
            mod = dt.date.fromisoformat(rec["modified_date"])
            ref = dt.datetime.fromisoformat(self.processed_at.replace("Z", "+00:00")).date()
        except ValueError:
            return {"status": "UNKNOWN", "rule": RULE_FRESHNESS}
        age = (ref - mod).days
        return {
            "status": "FRESH" if age <= days else "POSSIBLY_STALE",
            "ageDays": age,
            "thresholdDays": days,
            "rule": RULE_FRESHNESS,
            "note": "목록 수준 판정 — 실데이터 최신성이 아닙니다",
        }

    # ------------------------------------------------------------ compare
    def compare_datasets(self, record_ids: list[str]) -> dict:
        if len(record_ids) < 2:
            raise InvalidArgument("비교에는 2개 이상 필요", {"count": len(record_ids)})
        if len(record_ids) > MAX_COMPARE:
            raise TooManyDatasets(f"비교는 최대 {MAX_COMPARE}개", {"count": len(record_ids)})
        recs = []
        for rid in record_ids:
            row = self.conn.execute("SELECT * FROM datasets WHERE record_id = ?", (rid,)).fetchone()
            if row is None:
                raise DatasetNotFound(f"데이터셋을 찾을 수 없습니다: {rid}", {"recordId": rid})
            recs.append(row_to_record(row))

        fields = [
            ("listType", lambda r: r["list_type"]),
            ("orgName", lambda r: r["org_name"]),
            ("theme", lambda r: r["theme_raw"]),
            ("formats", lambda r: r["formats"]),
            ("updateCycle", lambda r: r["update_cycle"]),
            ("license", lambda r: r["license_code"]),
            ("modifiedDate", lambda r: r["modified_date"]),
            ("createdDate", lambda r: r["created_date"]),
            ("rowCount", lambda r: r["row_count"]),
            ("spatial", lambda r: r["spatial_raw"]),
            ("temporal", lambda r: r["temporal_raw"]),
            ("completenessScore", lambda r: r["completeness_score"]),
            ("keywords", lambda r: r["keywords"]),
            ("fee", lambda r: r["fee"]),
            ("apiType", lambda r: r["api_type"]),
        ]
        differences, shared = [], []
        for name, getter in fields:
            values = {r["record_id"]: getter(r) for r in recs}
            uniq = {json.dumps(v, ensure_ascii=False, sort_keys=True) for v in values.values()}
            if len(uniq) > 1:
                differences.append({"field": name, "values": values})
            else:
                shared.append({"field": name, "value": next(iter(values.values()))})

        data = {
            "datasets": [self._summary(r) for r in recs],
            "differences": differences,
            "sharedFields": shared,
            "note": "구조화된 사실 비교입니다. 목적별 의미 해석은 포함하지 않습니다(§4.1).",
        }
        warnings = []

        # 구조 비교(v1.3, S2) — 전원 관측된 경우에만. 원본 컬럼명 '정확 일치' 기준의 사실 비교
        cols_by_rid = {r["record_id"]: self._structure_columns_for(r["list_key"]) for r in recs}
        if all(v is not None for v in cols_by_rid.values()):
            sets = {rid: set(v) for rid, v in cols_by_rid.items()}
            common = sorted(set.intersection(*sets.values()))
            data["structureComparison"] = {
                "commonColumns": common[:50],
                "onlyIn": {rid: sorted(s - set(common))[:20] for rid, s in sets.items()},
                "columnCounts": {rid: len(s) for rid, s in sets.items()},
                "note": "원본 컬럼명 정확 일치 기준입니다 — 명칭이 달라도 같은 의미일 수 있고, "
                        "명칭이 같아도 의미 동일성·결합 가능성은 확인되지 않았습니다.",
            }
            data["structureComparisonRule"] = "structure-status-v1.0"
        elif any(v is not None for v in cols_by_rid.values()):
            warnings.append("일부 데이터셋만 구조가 관측되어 구조 비교는 생략되었습니다(미수집 ≠ 컬럼 없음).")

        return envelope(data, self.snapshot, [RULE_CARD], warnings)

    # ------------------------------------------------------------ changes
    def get_catalog_changes(
        self, status: str | None = None, cursor: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict:
        if status and status not in _CHANGE_STATUSES:
            raise InvalidArgument(f"status는 {_CHANGE_STATUSES} 중 하나", {"status": status})
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise InvalidArgument(f"pageSize는 1~{MAX_PAGE_SIZE}", {"pageSize": page_size})
        offset = decode_cursor(cursor, self.snapshot).get("o", 0) if cursor else 0

        where, params = [], []
        if status:
            where.append("status = ?")
            params.append(status)
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        total = self.conn.execute(
            f"SELECT COUNT(*) FROM changes {where_sql}", params
        ).fetchone()[0]
        rows = self.conn.execute(
            f"SELECT * FROM changes {where_sql} ORDER BY status, record_id LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        base = self.conn.execute(
            "SELECT base_snapshot FROM changes LIMIT 1"
        ).fetchone()

        warnings = []
        if total == 0 and base is None:
            warnings.append(
                "비교 기준 이전 스냅샷이 없습니다 — 첫 스냅샷이거나 diff 미생성 상태입니다."
            )
        items = [
            {
                "recordId": r["record_id"],
                "listKey": r["list_key"],
                "status": r["status"],
                "changedFields": json.loads(r["changed_fields"]) if r["changed_fields"] else None,
                "title": r["title"],
                "orgName": r["org_name"],
            }
            for r in rows
        ]
        has_more = offset + len(rows) < total
        # v1.6 additive: 상태별 집계 — 소비자가 '무엇이 얼마나 바뀌었는지'를 한 번에 본다
        summary = {
            r["status"]: r["n"]
            for r in self.conn.execute(
                "SELECT status, COUNT(*) AS n FROM changes GROUP BY status"
            ).fetchall()
        }
        data = {
            "baseSnapshot": base["base_snapshot"] if base else None,
            # v1.6 additive: 기준 부재 사유 코드 — null·0을 고장으로 오인하지 않게(§12)
            "baseUnavailableReason": None if base else "FIRST_SNAPSHOT_OR_DIFF_NOT_GENERATED",
            "currentSnapshot": self.snapshot,
            "summary": summary,
            "items": items,
            "nextCursor": encode_cursor({"s": self.snapshot, "o": offset + len(rows)}) if has_more else None,
            "hasMore": has_more,
            "totalEstimate": total,
        }
        return envelope(data, self.snapshot, [RULE_DIFF], warnings)

    # ------------------------------------------------------------ stats
    def get_catalog_stats(self, axis: str, limit: int = 30) -> dict:
        if axis not in _STATS_AXES:
            raise InvalidArgument(f"axis는 {_STATS_AXES} 중 하나", {"axis": axis})
        limit = min(max(limit, 1), 200)
        rules = []
        if axis == "theme":
            rows = self.conn.execute(
                "SELECT theme_top AS k, COUNT(*) AS n FROM datasets GROUP BY theme_top ORDER BY n DESC LIMIT ?",
                (limit,),
            ).fetchall()
            data = {"axis": axis, "buckets": [{"key": r["k"], "count": r["n"]} for r in rows]}
        elif axis == "org":
            rows = self.conn.execute(
                "SELECT org_name AS k, COUNT(*) AS n FROM datasets GROUP BY org_name ORDER BY n DESC LIMIT ?",
                (limit,),
            ).fetchall()
            data = {"axis": axis, "buckets": [{"key": r["k"], "count": r["n"]} for r in rows]}
        elif axis == "format":
            rows = self.conn.execute(
                "SELECT jf.value AS k, COUNT(*) AS n FROM datasets d, json_each(d.formats) jf "
                "GROUP BY jf.value ORDER BY n DESC LIMIT ?",
                (limit,),
            ).fetchall()
            data = {"axis": axis, "buckets": [{"key": r["k"], "count": r["n"]} for r in rows]}
        elif axis == "listType":
            rows = self.conn.execute(
                "SELECT list_type AS k, COUNT(*) AS n FROM datasets GROUP BY list_type ORDER BY n DESC"
            ).fetchall()
            data = {"axis": axis, "buckets": [{"key": r["k"], "count": r["n"]} for r in rows]}
        elif axis == "family":
            # v1.8 additive(ADR-011): 목록 수와 계열 후보 수의 구분 — 자동 후보
            # 비율이며 사람 검증 전 수치다. 도입 전 릴리스는 부재를 상태로 보고.
            rules = [RULE_FAMILY]
            if not self.families_available:
                data = {"axis": axis, "available": False,
                        "note": "이 릴리스에는 계열 후보 테이블이 없습니다(도입 전 빌드) — 0건이 아니라 미산출입니다."}
            else:
                total, member_records = self.conn.execute(
                    "SELECT COUNT(*), COALESCE(SUM(member_count), 0) FROM families"
                ).fetchone()
                by_evidence = {r["k"]: r["n"] for r in self.conn.execute(
                    "SELECT evidence_level AS k, COUNT(*) AS n FROM families GROUP BY 1")}
                by_review = {r["k"]: r["n"] for r in self.conn.execute(
                    "SELECT review_status AS k, COUNT(*) AS n FROM families GROUP BY 1")}
                file_total = self.conn.execute(
                    "SELECT COUNT(*) FROM datasets WHERE list_type='FILE'").fetchone()[0]
                data = {
                    "axis": axis, "available": True,
                    "familyCandidates": {
                        "families": total,
                        "memberRecords": member_records,
                        "fileRecordsTotal": file_total,
                        "byEvidenceLevel": by_evidence,
                        "byReviewStatus": by_review,
                    },
                    "note": "자동 탐지 후보 통계입니다 — 확정된 계열 수가 아니며, "
                            "목록 수와 계열 수는 서로 다른 단위입니다.",
                }
        else:  # completeness — 유형별 프로파일 기준(§4.1)
            rules = list(RULE_COMPLETENESS.values())
            buckets = []
            for profile in ("FILE", "API", "STD"):
                rows = self.conn.execute(
                    "SELECT CAST(completeness_score * 10 AS INTEGER) AS b, COUNT(*) AS n "
                    "FROM datasets WHERE completeness_profile = ? GROUP BY b ORDER BY b",
                    (profile,),
                ).fetchall()
                avg = self.conn.execute(
                    "SELECT AVG(completeness_score) FROM datasets WHERE completeness_profile = ?",
                    (profile,),
                ).fetchone()[0]
                buckets.append({
                    "profile": profile,
                    "rule": RULE_COMPLETENESS[profile],
                    "average": round(avg, 4) if avg is not None else None,
                    "histogram": [
                        {"range": f"{r['b'] / 10:.1f}~{(r['b'] + 1) / 10:.1f}", "count": r["n"]}
                        for r in rows
                    ],
                })
            data = {"axis": axis, "profiles": buckets}
        return envelope(data, self.snapshot, rules, [])

    # ------------------------------------------------------------ status/context
    def get_status(self) -> dict:
        ptr = read_current_pointer()
        counts = {
            "datasets": self.conn.execute("SELECT COUNT(*) FROM datasets").fetchone()[0],
            "issues": self.conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0],
            "changes": self.conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0],
        }
        data = {
            "currentSnapshot": self.snapshot,
            "release": self.release,
            "deployedAt": ptr.get("deployedAt"),
            "processedAt": self.processed_at,
            "counts": counts,
        }
        # v1.5 additive: 스냅샷 지연을 서버 사실로(§3.1 — 프론트 계산 회피).
        # 기준: 스냅샷 월 시작일 ~ 배포 시각.
        if data["deployedAt"] and self.snapshot:
            try:
                deployed = dt.datetime.fromisoformat(data["deployedAt"].replace("Z", "+00:00"))
                month_start = dt.datetime.fromisoformat(f"{self.snapshot}-01T00:00:00+00:00")
                data["snapshotLagDays"] = max(0, (deployed - month_start).days)
            except ValueError:
                pass
        if self.obs_conn:  # 구조 관측 커버리지(§12) — 스토어 배포 시에만
            total_file = self.conn.execute(
                "SELECT COUNT(*) FROM datasets WHERE list_type='FILE'").fetchone()[0]
            data["structureCoverage"] = {
                "recordsAvailable": len(self._structure_keys()),
                "fileRecordsTotal": total_file,
            }
        return envelope(data, self.snapshot, [], [])
