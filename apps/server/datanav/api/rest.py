"""3층 웹용 REST API — MCP와 동일한 Service를 사용(판단 로직 이중화 금지, §2).

보안(§10): rate limit, CORS, 입력 제한. 인증 없는 공개 읽기 전용 API.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Query, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from ..config import CURRENT_POINTER
from ..pipeline.jsonld import JSONLD_CONTEXT
from ..rules import load_registry
from .errors import HTTP_STATUS, DatanavError, RateLimited
from .mcp_server import _SHAPES_PATH, _PROMPTS_DIR
from .service import Service

# 운영 배포 시 환경변수로 제한: DATANAV_CORS_ORIGINS="https://datanav.example" (쉼표 구분)
# 로컬 기본값은 개발 편의를 위한 전체 허용이며, 다중 프로세스 환경에서는
# 프로세스 메모리 기반 rate limit 대신 프록시/게이트웨이 계층 제한을 병행해야 한다.
RATE_LIMIT_PER_MIN = int(os.environ.get("DATANAV_RATE_LIMIT_PER_MIN", "120"))
CORS_ORIGINS = [
    o.strip() for o in os.environ.get("DATANAV_CORS_ORIGINS", "*").split(",") if o.strip()
]
# 리버스 프록시(nginx 등) 뒤에서만 1로 설정 — 직접 노출 시 X-Forwarded-For는 위조 가능하다.
TRUST_PROXY = os.environ.get("DATANAV_TRUST_PROXY", "0") == "1"


def _client_ip(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    if TRUST_PROXY:
        # X-Real-IP는 신뢰 프록시(nginx)가 $remote_addr로 덮어쓰므로 위조 불가.
        # X-Forwarded-For는 클라이언트가 앞에 값을 심을 수 있어 마지막(프록시가 덧붙인) 값만 쓴다.
        real = request.headers.get("x-real-ip")
        fwd = request.headers.get("x-forwarded-for")
        if real:
            ip = real.strip()
        elif fwd:
            ip = fwd.split(",")[-1].strip()
    return ip


# 익명 식별자 HMAC 키(§10) — 공통 규칙은 usage.py가 단일 출처(REST·MCP 공용)
from .usage import anon_hmac_key as _anon_hmac_key  # noqa: E402

_ANON_HMAC_KEY = _anon_hmac_key()


def _client_key(request: Request) -> str:
    """IP의 익명 HMAC(§10) — 원 IP는 저장하지 않고 캡·지표 키로만 쓴다."""
    return hmac.new(_ANON_HMAC_KEY, _client_ip(request).encode(), hashlib.sha256).hexdigest()[:12]

app = FastAPI(title="공공데이터 렌즈 API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],  # POST는 컨시어지 전용
    allow_headers=["*"],
)

_service: Service | None = None
_service_release: str | None = None
_hits: dict[str, deque] = defaultdict(deque)
_hits_last_sweep = 0.0


def _svc() -> Service:
    global _service, _service_release
    ptr_release = None
    if CURRENT_POINTER.exists():
        ptr_release = json.loads(CURRENT_POINTER.read_text(encoding="utf-8"))["release"]
    if _service is None or ptr_release != _service_release:
        _service = Service()
        _service_release = _service.release
    return _service


# ---- §10 익명 사용 로그 — 지표(§12)의 원천. 원 IP·개인정보는 저장하지 않는다.
# 옵트아웃: DNT/Sec-GPC/X-Datanav-No-Log 헤더가 있으면 해당 요청은 아예 기록하지 않는다.
# 정책 전문: docs/개인정보_로그_고지_v1.0.md (웹 푸터·/api/resources/privacy로 공개)
USAGE_LOG_ENABLED = os.environ.get("DATANAV_USAGE_LOG", "1") == "1"
_log_lock = threading.Lock()


def _log_dir() -> Path:
    from .. import config
    return Path(os.environ.get("DATANAV_LOG_DIR", config.DATA_DIR / "logs"))


def _opted_out(request: Request) -> bool:
    from .usage import opted_out
    return opted_out(request.headers)


_RETENTION_DAYS = 365
_last_prune_day = ""


def _prune_old_logs(today: str) -> None:
    """§10 보존(12개월) 집행 — 월간 빌드 성공 여부와 무관하게 서비스가 스스로 지운다.
    하루 한 번, 로그 기록 경로에서 지연 실행(별도 cron 불필요)."""
    global _last_prune_day
    if today == _last_prune_day:
        return
    _last_prune_day = today
    cutoff = time.time() - _RETENTION_DAYS * 86400
    try:
        for p in _log_dir().glob("usage-*.jsonl"):
            if p.stat().st_mtime < cutoff:
                p.unlink(missing_ok=True)
    except OSError:
        pass  # 정리 실패가 본 응답을 막지 않는다


def _write_usage_log(request: Request, status_code: int, ms: int) -> None:
    path = request.url.path
    if not (path.startswith("/api/") or path.startswith("/projects/public-data-lens/")):
        return
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "path": path,
        "status": status_code,
        "ms": ms,
        # 익명 식별자(§10): 웹이 보낸 난수 ID 우선, 없으면 IP 단방향 해시 — 원 IP 미저장
        "anon": request.headers.get("x-datanav-anon-id", "")[:32] or _client_key(request),
    }
    extra = getattr(request.state, "log_extra", None)
    if extra:
        entry.update(extra)
    day = entry["ts"][:10]
    p = _log_dir() / f"usage-{day}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with _log_lock:
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _prune_old_logs(day)


@app.middleware("http")
async def usage_log(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    if USAGE_LOG_ENABLED and not _opted_out(request):
        try:
            _write_usage_log(request, response.status_code, int((time.monotonic() - start) * 1000))
        except Exception:
            pass  # 로그 실패가 본 응답을 막지 않는다
    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    global _hits_last_sweep
    ip = _client_ip(request)
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT_PER_MIN:
        err = RateLimited("요청 한도를 초과했습니다 — 잠시 후 다시 시도하세요",
                          {"limitPerMinute": RATE_LIMIT_PER_MIN})
        return JSONResponse(err.to_dict(), status_code=429)
    q.append(now)
    # 공개 배포에서 IP별 항목이 무한히 누적되지 않도록 만료 키를 주기적으로 정리
    if now - _hits_last_sweep > 300:
        _hits_last_sweep = now
        for k in [k for k, v in _hits.items() if k != ip and (not v or now - v[-1] > 60)]:
            del _hits[k]
    return await call_next(request)


@app.exception_handler(DatanavError)
async def datanav_error_handler(request: Request, exc: DatanavError):
    snapshot = _service.snapshot if _service else None
    return JSONResponse(exc.to_dict(snapshot), status_code=HTTP_STATUS[exc.code])


@app.get("/api/status")
def status():
    return _svc().get_status()


@app.get("/api/search")
def search(
    request: Request,
    query: str | None = None,
    theme: str | None = None,
    org: str | None = None,
    format: str | None = None,
    updateCycle: str | None = None,
    license: str | None = None,
    listType: str | None = None,
    region: str | None = None,
    includeInferred: bool = True,
    updatedAfter: str | None = None,
    cursor: str | None = None,
    pageSize: int = Query(default=20, ge=1, le=100),
    interpret: bool = False,
    sort: str | None = None,
):
    result = _svc().search_datasets(
        query=query, theme=theme, org=org, fmt=format, update_cycle=updateCycle,
        license_code=license, list_type=listType, region=region,
        include_inferred=includeInferred, updated_after=updatedAfter,
        cursor=cursor, page_size=pageSize, interpret=interpret, sort=sort,
    )
    # §12 지표용 주석 — 검색어 원문 정책은 고지문 참조(보존 12개월, 옵트아웃 시 미기록)
    filters = [k for k, v in [("theme", theme), ("org", org), ("format", format),
                              ("updateCycle", updateCycle), ("license", license),
                              ("listType", listType), ("region", region)] if v]
    request.state.log_extra = {
        "q": (query or "")[:200] or None,
        "zero": result["data"]["totalEstimate"] == 0,
        "filters": filters or None,
    }
    return result


@app.get("/api/datasets/{record_id}")
def dataset(record_id: str, view: str = "card"):
    return _svc().get_dataset(record_id, view)


@app.get("/api/search/columns")
def search_columns(
    keywords: str,
    pageSize: int = Query(default=20, ge=1, le=100),
):
    kws = [k.strip() for k in keywords.split(",") if k.strip()]
    return _svc().search_by_columns(kws, pageSize)


@app.get("/api/datasets/{record_id}/structure")
def dataset_structure(
    record_id: str,
    includeExamples: bool = True,
    maxExamples: int = Query(default=10, ge=1, le=10),
):
    return _svc().get_dataset_structure(record_id, includeExamples, maxExamples)


@app.get("/api/compare")
def compare(ids: str):
    record_ids = [i.strip() for i in ids.split(",") if i.strip()]
    return _svc().compare_datasets(record_ids)


@app.get("/api/changes")
def changes(
    status: str | None = None,
    cursor: str | None = None,
    pageSize: int = Query(default=20, ge=1, le=100),
):
    return _svc().get_catalog_changes(status, cursor, pageSize)


@app.get("/api/stats")
def stats(axis: str, limit: int = 30):
    return _svc().get_catalog_stats(axis, limit)


# 공개 Resource의 HTTP 사본(정본 경로는 §7 — 배포 시 리버스 프록시로 연결)
@app.get("/api/resources/rules")
def resource_rules():
    return load_registry()


@app.get("/api/resources/context")
def resource_context():
    return {"@context": JSONLD_CONTEXT}


@app.get("/api/resources/shapes", response_class=PlainTextResponse)
def resource_shapes():
    return _SHAPES_PATH.read_text(encoding="utf-8")


@app.get("/api/resources/prompts/build-data-plan", response_class=PlainTextResponse)
def resource_prompt():
    return (_PROMPTS_DIR / "build-data-plan-v1.0.md").read_text(encoding="utf-8")


@app.get("/api/resources/privacy", response_class=PlainTextResponse)
def resource_privacy():
    """§10 로그·개인정보 고지 전문 (docs/개인정보_로그_고지_v1.1.md — MCP 사용 로그 신설)."""
    from .. import config
    p = config.PROJECT_ROOT / "docs" / "개인정보_로그_고지_v1.1.md"
    return PlainTextResponse(p.read_text(encoding="utf-8"), media_type="text/markdown; charset=utf-8")


@app.get("/api/resources/spec/tools")
def resource_tool_spec():
    from pathlib import Path
    from ..config import SCHEMA_VERSION
    spec_path = Path(__file__).resolve().parents[1] / "spec" / f"tool-schemas-v{SCHEMA_VERSION}.json"
    return json.loads(spec_path.read_text(encoding="utf-8"))


@app.get("/api/resources/eval")
def resource_eval():
    """검색 품질 지표(§3.2, v1.5) — golden/eval_report.json 읽기 전용 노출.
    humanReviewed=false(자동 생성 골든셋 v0)를 그대로 전달한다 — 소비자는 함께 표기할 것."""
    from pathlib import Path
    from .errors import DatasetNotFound
    p = Path(__file__).resolve().parents[2] / "golden" / "eval_report.json"
    if not p.exists():
        raise DatasetNotFound("평가 리포트가 아직 생성되지 않았습니다", {"resource": "eval"})
    return json.loads(p.read_text(encoding="utf-8"))


class PlanRequest(BaseModel):
    """POST /api/plan 입력 — build_data_plan Tool과 동일 의미(§12, v1.5)."""
    purpose: str
    region: str | None = None
    maxCandidates: int = 5


@app.post("/api/plan")
def plan(req: PlanRequest, request: Request):
    """활용 계획 초안(v1.5) — plan.py build_plan()의 REST 노출. 새 판정 없음:
    MCP build_data_plan Tool과 같은 결정론 조립기를 호출한다(planStatus=DRAFT 고정)."""
    from .plan import build_plan
    result = build_plan(_svc(), purpose=req.purpose, region=req.region,
                        max_candidates=req.maxCandidates)
    request.state.log_extra = {"q": req.purpose[:200], "filters": ["plan"]}
    return result


# ---- §7 정본 URI 디레퍼런싱 — https://service.datahub.kr/projects/public-data-lens/... 경로가
# 실제로 해소되도록 정본 표현을 반환한다(Cool URIs). 배포 시 nginx가 이 경로를 그대로 전달한다.
from fastapi.responses import FileResponse, RedirectResponse, Response  # noqa: E402

from ..config import RELEASES_DIR  # noqa: E402

_CANON = "/projects/public-data-lens"


def _ld(doc: dict) -> Response:
    return Response(json.dumps(doc, ensure_ascii=False, indent=2),
                    media_type="application/ld+json")


@app.get(_CANON + "/context/catalog/1.0")
def canon_context():
    return _ld({"@context": JSONLD_CONTEXT})


@app.get(_CANON + "/rules/catalog/1.0")
def canon_rules():
    return load_registry()


@app.get(_CANON + "/shapes/catalog/1.0")
def canon_shapes():
    return Response(_SHAPES_PATH.read_text(encoding="utf-8"), media_type="text/turtle")


@app.get(_CANON + "/prompts/build-data-plan/1.0")
def canon_prompt():
    return Response((_PROMPTS_DIR / "build-data-plan-v1.0.md").read_text(encoding="utf-8"),
                    media_type="text/markdown")


@app.get(_CANON + "/spec/tools/1.0")
def canon_spec():
    return resource_tool_spec()


@app.get(_CANON + "/dataset/{list_key}")
def canon_dataset(list_key: str, request: Request):
    """Dataset 정본 URI 해소. 기본 표현은 JSON-LD.
    브라우저(text/html)는 원문 접근 원칙에 따라 공공데이터포털로 303 연결한다."""
    from .errors import DatasetNotFound

    svc = _svc()
    rows = svc.conn.execute(
        "SELECT record_id, list_type, list_url FROM datasets WHERE list_key = ? "
        "ORDER BY CASE list_type WHEN 'FILE' THEN 0 WHEN 'API' THEN 1 ELSE 2 END",
        (list_key,),
    ).fetchall()
    if not rows:
        raise DatasetNotFound(f"데이터셋을 찾을 수 없습니다: {list_key}", {"listKey": list_key})

    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/ld+json" not in accept and rows[0]["list_url"]:
        return RedirectResponse(rows[0]["list_url"], status_code=303)

    # 이중 등재(FILE/API)는 동일 데이터셋의 복수 제공 형태 — 대표(FILE 우선) 레코드 기준 문서를 반환
    doc = svc.get_dataset(rows[0]["record_id"], "jsonld")["data"]["dataset"]
    return _ld(doc)


def _release_dir(svc: Service, snapshot: str) -> Path:
    from .errors import SnapshotNotFound

    if snapshot not in ("current", svc.snapshot):
        raise SnapshotNotFound(
            f"호스팅 대상은 현재 스냅샷({svc.snapshot})뿐입니다 — 과거분은 벌크 아카이브로 제공",
            {"snapshot": snapshot},
        )
    return RELEASES_DIR / svc.release


@app.get(_CANON + "/catalog/{snapshot}")
def canon_catalog(snapshot: str):
    svc = _svc()
    p = _release_dir(svc, snapshot) / "catalog.jsonld"
    return _ld(json.loads(p.read_text(encoding="utf-8")))


@app.get(_CANON + "/catalog/{snapshot}/aird-assessment")
def canon_aird(snapshot: str):
    svc = _svc()
    p = _release_dir(svc, snapshot) / f"aird-assessment-{svc.snapshot}.jsonld"
    return _ld(json.loads(p.read_text(encoding="utf-8")))


@app.get(_CANON + "/catalog/{snapshot}/record/{record_id}")
def canon_catalog_record(snapshot: str, record_id: str):
    """CatalogRecord 정본 URI 해소 — JSON-LD가 발행하는 @id와 동일한 REST 표면."""
    svc = _svc()
    _release_dir(svc, snapshot)
    return _ld(svc.get_catalog_record(record_id))


@app.get(_CANON + "/catalog/{snapshot}/files/{filename}")
def canon_bulk(snapshot: str, filename: str):
    """벌크 정본(NDJSON+gzip 등) 내려받기 — 릴리스 디렉터리의 산출물만 허용."""
    from .errors import DatasetNotFound

    svc = _svc()
    base = _release_dir(svc, snapshot)
    p = (base / filename).resolve()
    allowed = p.parent == base.resolve() and (
        p.suffix in (".jsonld", ".json") or p.name.endswith(".ndjson.gz")
    )
    if not allowed or not p.exists():
        raise DatasetNotFound(f"제공하지 않는 파일: {filename}", {"filename": filename})
    media = "application/gzip" if p.name.endswith(".gz") else (
        "application/ld+json" if p.suffix == ".jsonld" else "application/json")
    return FileResponse(p, media_type=media, filename=p.name)


# ---- M3 생성형 컨시어지(§9 3층) — 별도 서비스(B 스택) 표면. 모듈이 있을 때만 라우트가
# 등록되며, 공개 스냅샷(concierge*.py 미포함)에서는 import 실패로 자동 비활성된다.
# A 배포는 모듈이 있어도 DATANAV_CONCIERGE_ENABLED=0으로 표면을 끈다(게이트웨이 404와 이중 방어).
try:
    from . import concierge_routes as _concierge_routes  # noqa: E402
except ImportError:  # 공개 스냅샷 — 컨시어지 구현 미포함
    _concierge_routes = None

if _concierge_routes is not None:
    _concierge_routes.register(app, client_key=_client_key)


# ---- 대표 활용 사례 6개(§9 2층 산출물) — 서술은 정적, 후보 카드는 조회 시점에 실데이터로 보강
from pathlib import Path as _Path  # noqa: E402

_CASES_DIR = _Path(__file__).resolve().parents[1] / "cases"


def _load_case(case_id: str) -> dict | None:
    p = _CASES_DIR / f"{case_id}.json"
    if not p.exists() or not p.name.startswith("case-"):
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/cases")
def list_cases():
    svc = _svc()
    items = []
    for p in sorted(_CASES_DIR.glob("case-*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        items.append({
            "id": c["id"], "title": c["title"], "purpose": c["purpose"],
            "sourceSnapshot": c["metadata"]["sourceSnapshot"],
            "humanReviewed": c["metadata"]["humanReviewed"],
            "candidateCount": len(c["candidates"]),
        })
    from .envelope import envelope
    return envelope({"items": items}, svc.snapshot, [], [
        "사례는 작성 시점 스냅샷 기준의 편집 산출물이며, 후보 데이터셋 카드는 현재 스냅샷으로 재조회됩니다."
    ])


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    from .envelope import envelope
    from .errors import DatasetNotFound

    case = _load_case(case_id)
    if case is None:
        return JSONResponse(
            {"error": {"code": "DATASET_NOT_FOUND", "message": f"사례 없음: {case_id}",
                       "details": {}, "sourceSnapshot": None}}, status_code=404)
    svc = _svc()
    warnings = []
    enriched = []
    for cand in case["candidates"]:
        entry = dict(cand)
        try:
            card = svc.get_dataset(cand["recordId"], "card")["data"]["dataset"]
            entry["card"] = {
                "title": card["title"], "orgName": card["orgName"],
                "listType": card["listType"], "formats": card["formats"],
                "updateCycle": card["updateCycleRaw"], "modifiedDate": card["modifiedDate"],
                "completeness": card["completeness"], "freshness": card["freshness"],
                "portalUrl": card["portal"]["listUrl"],
            }
            entry["presentInCurrentSnapshot"] = True
        except DatasetNotFound:
            entry["presentInCurrentSnapshot"] = False
            warnings.append(
                f"후보 {cand['recordId']}가 현재 스냅샷({svc.snapshot})에 없습니다 — 사례 재검증 필요"
            )
        enriched.append(entry)
    data = dict(case)
    data["candidates"] = enriched
    data["currentSnapshot"] = svc.snapshot
    if case["metadata"]["sourceSnapshot"] != svc.snapshot:
        warnings.append(
            f"사례 작성 스냅샷({case['metadata']['sourceSnapshot']})과 현재 스냅샷({svc.snapshot})이 다릅니다."
        )
    if not case["metadata"]["humanReviewed"]:
        warnings.append("본 사례는 인간 검토 전 초안입니다(§9 재현성 메타데이터).")
    return envelope(data, svc.snapshot, [], warnings)
