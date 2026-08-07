# 공공데이터 렌즈

> **하고 싶은 일을 말하면, 활용할 공공데이터와 선택 근거를 찾아주는 AI 탐색·판단 계층**

![snapshot](https://img.shields.io/badge/스냅샷-2026--06-blue)
![contract](https://img.shields.io/badge/MCP%20계약-v1.0.0%20동결%20%2B%20v1.6.0%20additive-success)
![status](https://img.shields.io/badge/서비스-v1.1%20beta-orange)
![license](https://img.shields.io/badge/license-MIT-green)

**English** — *Public Data Lens* is a discovery-and-judgment layer over Korea's open data portal ([data.go.kr](https://www.data.go.kr)): the monthly catalog (~96k listings) normalized into canonical JSON-LD/DCAT with versioned deterministic quality rules, exposed to AI hosts via the Model Context Protocol. It is an independent open-source implementation that predates the draft AIRD (AI-Ready Data) standard and serves as a reference implementation for it. Connector: `https://service.datahub.kr/projects/public-data-lens/mcp`

## 무엇인가

- **서비스로서** — 행정안전부 공공데이터포털 위에 얹는 **탐색·판단 계층**입니다. 어떤 데이터가 존재하고 어떤 후보가 검토할 가치가 있는지를 근거와 함께 제시합니다. 포털을 대체하지 않으며 원문 접근은 항상 포털로 연결합니다.
- **연구로서** — **AIRD(AI-Ready Data) 표준 논의에 앞서 개발된 독립 오픈소스 구현**이며, 표준안의 실현 가능성을 검증하는 참조 구현으로 활용됩니다. 월간 목록을 정본 JSON-LD(DCAT)로 정규화하고 SHACL 검증과 버전 관리되는 판정 규칙을 통해 "표준이 실제로 동작함"을 보입니다.

**책임 분리 원칙** — 재현되어야 하는 판정(정규화·완전성·사실 비교·랭킹)은 서버가 결정론적으로 수행하고, 목적에 따른 해석은 연결된 호스트 LLM이 수행합니다. 반복 분석과 값 수준 검증을 수행하는 생성형 AI 컨시어지는 별도 서비스이며 이 저장소에 포함되지 않습니다.

**이해관계 고지** — 이 서비스를 기반으로 하는 상용 AI 컨시어지가 별도 법인에서 제공됩니다. 렌즈는 MIT 라이선스로 누구에게나 동일하게 공개되며, 특정 사업자에게 우선 접근이나 비공개 엔드포인트를 제공하지 않습니다.

## 어떻게 쓰나

인증 없이 **URL 등록만으로** 사용하는 읽기 전용 무료 서비스입니다.

```text
https://service.datahub.kr/projects/public-data-lens/mcp
```

1. Claude 웹/앱 → **설정 → 커넥터 → 커스텀 커넥터 추가**
2. 위 주소 등록
3. 대화에서 공공데이터 렌즈 선택

ChatGPT 개발자 모드에서도 같은 주소를 `No Authentication`으로 등록할 수 있습니다. Claude Code 등 개발 도구는 `.mcp.json`에 등록합니다.

```json
{
  "mcpServers": {
    "public-data-lens": {
      "type": "http",
      "url": "https://service.datahub.kr/projects/public-data-lens/mcp"
    }
  }
}
```

### 이렇게 질문해 보세요

* “폐교 활용 사업을 검토 중인데 참고할 공공데이터를 찾아줘.”
* “고령자 의료 접근성 분석에 필요한 데이터 후보를 비교해줘.”
* “위도와 경도 컬럼이 있는 전기차 충전소 데이터를 찾아줘.”
* “이 데이터셋의 실제 파일에는 어떤 컬럼이 있는지 보여줘.”
* “지난달 공공데이터 목록에서 사라진 데이터가 있어?” — 변경 추적은 월간 스냅샷이
  2개 이상 축적된 뒤부터 결과가 나옵니다(현재 첫 스냅샷 축적 단계 — 응답이
  `baseSnapshot: null`과 함께 그 사실을 알려줍니다).
* “이 목적에 필요한 데이터와 예상 결합 항목을 계획으로 만들어줘.”

목적만 말해도 됩니다. `build_data_plan`이 필요한 데이터 역할을 나누고 후보·선정 근거·예상 결합 항목·확인할 한계를 **활용 계획 초안**으로 반환합니다. 생성형 AI를 쓰지 않는 결정론적 Tool이며 결과는 항상 `DRAFT`입니다.

### 제공 기능

| 구분 | 이름 | 요지 |
| --- | --- | --- |
| Tool | `search_datasets` | 키워드 + 분류·기관·포맷·주기·라이선스·유형·지역·수정일 필터, 커서 페이징 |
| Tool | `get_dataset` | 단건 조회 — `card`(판단 요약) / `normalized` / `source` / `jsonld`(정본) |
| Tool | `compare_datasets` | 최대 5개의 구조화된 사실 비교 (해석 없음) |
| Tool | `get_catalog_changes` | 월별 변경 추적 — 6개 상태, **스냅샷 부재 ≠ 폐기** |
| Tool | `get_catalog_stats` | 주제·기관·포맷·완전성·유형 통계 |
| Tool | `search_by_columns` | 원본 컬럼 기준 검색 — 예: `['위도','경도']`, 일치 근거 동반 |
| Tool | `get_dataset_structure` | 실파일에서 관측한 구조 — 컬럼·유형·예시값(안전 게이트 통과분) |
| Tool | `get_context` | (호환) 서비스 개요·스냅샷·규칙 요약 |
| Tool | `build_data_plan` | 목적 문장 → 활용 계획 초안. 결정론, 항상 `DRAFT` |
| Prompt | `build_data_plan` / `compare_for_purpose` | Tool 결과의 대화형 설명 / 목적 관점 비교 절차 표준화 |
| Resource | 판정 규칙 · JSON-LD Context · SHACL · Tool 스키마 | 정본 URI로도 해소 |

## 무엇을 믿을 수 있나

모든 판정에는 근거 수준이 함께 표기됩니다.

| 근거 수준 | 의미 |
| --- | --- |
| `CATALOG_METADATA_ONLY` | 포털 목록 메타데이터에 근거 (검색·상세·비교·변경 이력) |
| `FILE_OBSERVATION` | 수집한 실파일의 구조를 직접 관측 (컬럼·유형·예시값) |
| `DRAFT` | 활용 계획 초안이며 실제 품질 검증 전 |
| `CANDIDATE_ONLY` | 예상 결합 항목으로 값 수준의 결합 가능성은 미확인 |

어느 수준이든 실제 데이터의 내용·품질·결합 가능성은 보증하지 않으며, 최종 확인은 공공데이터포털 원문에서 이루어집니다. `MISSING_FROM_SNAPSHOT`은 특정 월 목록에서 관측되지 않았다는 관찰 사실일 뿐이며, 폐기 확정은 `OFFICIALLY_WITHDRAWN`으로만 표기합니다.

**공통 계약** — 모든 응답은 `{ data, meta: { sourceSnapshot, processedAt, schemaVersion, ruleVersions[] }, warnings[] }` 봉투와 일관된 오류 모델을 사용합니다. 기반 계약 v1.0.0은 동결되어 있고 v1.6.0까지 하위 호환적인 additive 확장만 적용했습니다. 전문은 [부속명세 v1.0](docs/부속명세_v1.0.md)을 참고하세요.

**공정 사용** — 베타 기간의 공개 서비스로 SLA 없이 제공되며, IP당 2 req/s(순간 20회 버스트)로 제한됩니다. 대량 분석은 벌크 파일(`.ndjson.gz`)을 이용하세요.

**로그와 옵트아웃** — 원 IP를 저장하지 않는 익명 로그를 기록합니다. 검색어 원문이 포함될 수 있으므로 개인정보를 입력하지 마세요. DNT/GPC 또는 `X-Datanav-No-Log: 1` 헤더가 있으면 전혀 기록하지 않습니다. 전문: [개인정보·로그 고지](docs/개인정보_로그_고지_v1.1.md)

**오류 제보** — 목록 메타데이터의 오류 의심은 GitHub Issue로 알려주세요. 검토 후 데이터 제공 기관에 환류합니다.

## 셀프 호스팅

LLM API 키 없이 Docker 스택 하나로 배포합니다. 보안 필수 env 2종은 미지정 시 기동이 실패합니다.

> **주의**: 저장소에는 공공데이터포털 원본 CSV와 생성된 카탈로그 DB가 포함되지 않습니다. [목록개방현황 CSV](https://www.data.go.kr)를 내려받아 최초 빌드를 수행해야 합니다.

```bash
cp .env.example .env               # GATEWAY_REAL_IP_FROM(LB 대역)·DATANAV_MCP_ALLOWED_HOSTS 설정
sudo chown -R 10001:10001 data     # 비루트 컨테이너(uid 10001)
mkdir -p data/raw/incoming && cp <목록개방현황.csv> data/raw/incoming/
docker compose -f docker-compose.prod.yml run --rm api \
  python scripts/build_catalog.py /app/data/raw/incoming/<목록개방현황.csv> <YYYY-MM>
docker compose -f docker-compose.prod.yml up -d --build
```

절차와 운영 전제 전문은 [배포 설명서 v1.0](docs/배포_설명서_v1.0.md)에 있습니다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [설계서 v1.0 확정판](docs/공공데이터_내비게이터_설계서_v1.0_확정판.md) | 아키텍처·데이터 모델·규칙·운영 (동결) |
| [부속명세 v1.0](docs/부속명세_v1.0.md) | Tool별 JSON Schema 전문 + 공통 계약 |
| [매핑표 v1.0](docs/매핑표_v1.0.md) | 원본 CSV → 정규화 필드 매핑 (공개 산출물) |
| [배포 설명서 v1.0](docs/배포_설명서_v1.0.md) | 설치·운영 매뉴얼 |
| [호환성 확인 v1.0](docs/호환성_확인_v1.0.md) | MCP 클라이언트 호환성 기록 |
| [개인정보·로그 고지 v1.1](docs/개인정보_로그_고지_v1.1.md) | 익명 로그·옵트아웃 정책 |

정본(기계 판독용): [Tool 스키마](https://service.datahub.kr/projects/public-data-lens/spec/tools/1.0) · [판정 규칙](https://service.datahub.kr/projects/public-data-lens/rules/catalog/1.0) · [JSON-LD Context](https://service.datahub.kr/projects/public-data-lens/context/catalog/1.0) · [SHACL](https://service.datahub.kr/projects/public-data-lens/shapes/catalog/1.0)

## 출처 · 라이선스 · 인용

* **데이터 출처**: 행정안전부 [공공데이터포털](https://www.data.go.kr) 목록개방현황(월간). 본 저장소는 목록 메타데이터의 가공물만 포함하며 실데이터를 재배포하지 않습니다.
* **라이선스**: [MIT](LICENSE) — 코드와 공개 산출물(매핑표·판정 규칙·Context·SHACL)에 적용
* **인용**: [`CITATION.cff`](CITATION.cff) 참조 또는 저장소 URL 명시
* **문의 및 오류 제보**: GitHub Issues
