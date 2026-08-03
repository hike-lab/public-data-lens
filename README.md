# 공공데이터 렌즈

> **하고 싶은 일을 말하면 AI Ready 관점으로 정밀하게 투영하는 공공데이터 초점 레이어**

![snapshot](https://img.shields.io/badge/%EC%8A%A4%EB%83%85%EC%83%B7-2026--06-blue)
![datasets](https://img.shields.io/badge/%EB%8D%B0%EC%9D%B4%ED%84%B0%EC%85%8B-96%2C056%EA%B1%B4-informational)
![contract](https://img.shields.io/badge/MCP%20%EA%B3%84%EC%95%BD-v1.0.0%20%EB%8F%99%EA%B2%B0%20%2B%20v1.3.0%20additive-success)
![status](https://img.shields.io/badge/%EC%83%81%ED%83%9C-v1.0%20beta-orange)
![license](https://img.shields.io/badge/license-MIT-green)

> 본 결과는 공공데이터포털 목록 개방 데이터 기반이며 실제 데이터의 내용·품질·결합 가능성을
> 보증하지 않습니다. 공공데이터포털을 대체하지 않으며 모든 원문 접근은 포털로 연결합니다.

**English** — *Public Data Lens* is a discovery-and-judgment layer for Korea's open data portal
([data.go.kr](https://www.data.go.kr)): the portal's monthly catalog (~96k listings) as a
canonical JSON-LD/DCAT layer with versioned deterministic quality rules, exposed to AI hosts
via the **Model Context Protocol**, and a research testbed for the draft AIRD (AI-Ready Data)
standard. Connector URL: `https://service.datahub.kr/projects/public-data-lens/mcp`

## 빠른 시작 — Claude에 연결하기

인증 없이 **URL 등록만으로** 사용할 수 있습니다 (읽기 전용, 무료). 베타 기간의 공개 서비스로
SLA 없이 제공되며, 과도한 사용은 예고 없이 제한될 수 있습니다 — 대량 분석은 벌크
파일(`.ndjson.gz`)을 이용하세요. API 안정성은 계약 버전(v1.0.0 동결 + additive) 범위에서
유지됩니다.

1. Claude 웹/앱 → **[설정] → [커넥터] → [커스텀 커넥터 추가]**
2. `https://service.datahub.kr/projects/public-data-lens/mcp` 입력
3. 대화에서 바로 사용:
   - *"폐교 활용 사업을 검토 중인데 참고할 공공데이터 찾아줘"*
   - *"고령자 의료 접근성 분석에 쓸 데이터 후보를 비교해줘"*
   - *"지난달 공공데이터 목록에서 사라진 데이터가 있어?"*

더 정형화된 결과가 필요하면 프롬프트 메뉴에서 **`build_data_plan`** 을 선택하세요 — 호스트
LLM이 목적 분해→검색→비교→예상 결합 키→포털 링크의 표준 절차를 따르도록 안내하는 MCP
Prompt입니다(서버가 스스로 계획을 수립하거나 결합 가능성을 확정하지는 않습니다).

Claude Code 등 개발 도구는 `.mcp.json`에 등록합니다:

```json
{
  "mcpServers": {
    "public-data-lens": { "type": "http", "url": "https://service.datahub.kr/projects/public-data-lens/mcp" }
  }
}
```

## 제공 기능

| 구분 | 이름 | 요지 |
|---|---|---|
| Tool | `search_datasets` | 키워드 + 분류·기관·포맷·주기·라이선스·유형·지역·수정일 필터, 커서 페이징 |
| Tool | `get_dataset` | 단건 조회 — `card`(판단 요약) / `normalized` / `source`(원본) / `jsonld`(정본) |
| Tool | `compare_datasets` | 최대 5개의 구조화된 사실 비교 (해석 없음) |
| Tool | `get_catalog_changes` | 월별 변경 추적 — 6개 상태, **스냅샷 부재 ≠ 폐기** |
| Tool | `get_catalog_stats` | 주제·기관·포맷·완전성·유형 통계 |
| Tool | `search_by_columns` | 원본 컬럼(변수) 기준 검색 — 예: `['위도','경도']`, 일치 근거 동반 |
| Tool | `get_dataset_structure` | 실파일에서 관측한 구조 조회 — 컬럼·유형·예시값(안전 게이트 통과분) |
| Tool | `get_context` | (호환) 서비스 개요·스냅샷·규칙 요약 |
| Prompt | `build_data_plan` / `compare_for_purpose` | 활용 계획 수립 / 목적 관점 비교의 절차 표준화 |
| Resource | 판정 규칙 · JSON-LD Context · SHACL · Tool 스키마 | 정본 URI로도 해소 |

**공통 계약** — 기반 v1.0.0(동결) + 확장 v1.3.0(additive): 응답 봉투
`{ data, meta: { sourceSnapshot, processedAt, schemaVersion, ruleVersions[] }, warnings[] }`,
일관된 오류 모델, 모든 판정에 규칙 버전 표기. 전문: [부속명세 v1.0](docs/부속명세_v1.0.md)

## 무엇인가

- **서비스로서** — 공공데이터포털 위의 **탐색·판단 계층**. 어떤 데이터가 존재하고 어떤 후보가
  검토할 가치가 있는지를 근거와 함께 제시하며, 포털을 대체하지 않습니다.
- **연구로서** — 중앙대학교 HIKE 연구실의 **AIRD(AI-Ready Data) 표준안 실증** 프로젝트.
  월간 목록을 정본 JSON-LD(DCAT)로 정규화하고 SHACL 검증·버전 관리되는 판정 규칙으로
  "표준이 실제로 동작함"을 보여줍니다.

**책임 분리 원칙**: 재현되어야 하는 판정(정규화·완전성·사실 비교·랭킹)은 서버가 결정론적으로
수행하고, 목적 의존적 해석은 호스트 LLM이 수행합니다. 생성형 AI 컨시어지는 **별도 서비스**로
제공되며 이 저장소에 포함되지 않습니다.

## 사용자 가이드라인

- **기능에 따라 근거 수준이 다릅니다.** 검색·상세·비교·변경 이력은 포털 목록 메타데이터
  기반(`CATALOG_METADATA_ONLY`), 구조가 수집된 파일의 컬럼·예시값은 `FILE_OBSERVATION`으로
  표시됩니다. 어느 쪽이든 실제 데이터의 내용·품질은 반드시 포털 원문에서 확인하세요.
- **스냅샷 부재는 폐기가 아닙니다.** `MISSING_FROM_SNAPSHOT`은 관찰 사실이며, 폐기 확정은
  `OFFICIALLY_WITHDRAWN`으로만 표기됩니다.
- **검색어에 개인정보를 입력하지 마세요.** 검색어 원문은 품질 개선 목적의 익명 로그에 기록될
  수 있습니다.
- **공정 사용**: IP당 2 req/s(순간 20회 버스트). 대량 분석은 벌크 파일(`.ndjson.gz`)을 이용하세요.
- **로그와 옵트아웃**: 원 IP를 저장하지 않는 익명 로그를 기록하며, DNT/GPC 또는
  `X-Datanav-No-Log: 1` 헤더가 있으면 전혀 기록하지 않습니다.
  전문: [개인정보·이용 로그 고지](docs/개인정보_로그_고지_v1.0.md)
- **오류 제보 환영**: 목록 메타데이터의 오류 의심은 GitHub Issue로 알려주세요 — 검토 후
  데이터 제공 기관에 환류합니다.

## 셀프 호스팅

Docker 스택 하나로 배포합니다(LLM API 키 불필요). 보안 필수 env 2종은 미지정 시 기동이
실패합니다. 절차·운영 전제 전문: [배포 설명서](docs/배포_설명서_v1.0.md)

> **주의**: 저장소에는 공공데이터포털 원본 CSV와 생성된 카탈로그 DB가 포함되지 않습니다.
> 셀프 호스팅 시 [목록개방현황 CSV](https://www.data.go.kr)를 내려받아 최초 빌드를 수행해야 합니다.

```bash
cp .env.example .env               # GATEWAY_REAL_IP_FROM(LB 대역)·DATANAV_MCP_ALLOWED_HOSTS 설정
sudo chown -R 10001:10001 data     # 비루트 컨테이너(uid 10001)
mkdir -p data/raw/incoming && cp <목록개방현황.csv> data/raw/incoming/
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml run --rm api \
  python scripts/build_catalog.py /app/data/raw/incoming/<목록개방현황.csv> <YYYY-MM>
docker compose -f docker-compose.prod.yml up -d --build
```

## 문서

| 문서 | 내용 |
|---|---|
| [설계서 v1.0 확정판](docs/공공데이터_내비게이터_설계서_v1.0_확정판.md) | 아키텍처·데이터 모델·규칙·운영 (동결) |
| [부속명세 v1.0](docs/부속명세_v1.0.md) | Tool별 JSON Schema 전문 + 공통 계약 |
| [매핑표 v1.0](docs/매핑표_v1.0.md) | 원본 CSV → 정규화 필드 매핑 (공개 산출물) |
| [배포 설명서 v1.0](docs/배포_설명서_v1.0.md) | 설치·운영 매뉴얼 |
| [호환성 확인 v1.0](docs/호환성_확인_v1.0.md) | MCP 클라이언트 호환성 기록 |
| [개인정보·로그 고지 v1.0](docs/개인정보_로그_고지_v1.0.md) | 익명 로그·옵트아웃 정책 |

정본(기계 판독용): [Tool 스키마](https://service.datahub.kr/projects/public-data-lens/spec/tools/1.0) ·
[판정 규칙](https://service.datahub.kr/projects/public-data-lens/rules/catalog/1.0) ·
[JSON-LD Context](https://service.datahub.kr/projects/public-data-lens/context/catalog/1.0) ·
[SHACL](https://service.datahub.kr/projects/public-data-lens/shapes/catalog/1.0)

## 데이터 출처 · 라이선스 · 인용

- **데이터 출처**: 행정안전부 [공공데이터포털](https://www.data.go.kr) 목록개방현황(월간).
  본 저장소는 목록 **메타데이터의 가공물**만 포함하며 실데이터를 재배포하지 않습니다.
- **라이선스**: [MIT](LICENSE) — 코드와 공개 산출물(매핑표·판정 규칙·Context·SHACL)에 적용.
- **인용**: [`CITATION.cff`](CITATION.cff) 참조 또는 저장소 URL 명시.
- **개발 이력**: [haklaekim/public-data-lens](https://github.com/haklaekim/public-data-lens)
  (이 저장소는 릴리스 스냅샷입니다)
- **문의 및 오류 제보**: GitHub Issues
