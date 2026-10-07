// 인터페이스 문안 — 한국어(정본). 키 집합은 strings.en.jsx와 동일해야 한다(i18n.test.js).
// 값은 문자열('{name}' 자리 채움), 함수(어순·조건이 있는 문장, JSX 조각), 배열·객체 중 하나.
// 서버가 준 값은 여기 두지 않는다 — 데이터셋 제목·기관명·warnings[] 등은 원문 그대로 렌더한다.
// 검색 예시 질의(q)는 한국어 카탈로그를 조회하므로 두 언어에서 같고, 표시 문안(label)만 다르다.

export const STRINGS_KO = {
  // ---- 공통
  'common.loading': '불러오는 중…',

  // ---- 언어 전환
  'lang.aria': '표시 언어',
  'lang.ko': '한국어',
  'lang.en': 'English',

  // ---- App(상단·푸터·비교 바)
  'nav.concierge': 'AI 컨시어지',
  'nav.explore': '둘러보기',
  'nav.observatory': '관측 현황',
  'nav.about': '소개',
  'nav.connect': 'MCP 연결',
  'app.brandHome': 'Public Data Lens 홈',
  'app.navAria': '보조 메뉴',
  'app.backToSearch': '← 데이터 찾기로',
  'app.selectedCount': '{n}개 선택',
  'app.compareGo': '비교하기 →',
  'app.compareClear': '비우기',
  'app.conciergeOpen': 'AI 컨시어지 열기',
  'app.footerDisclaimer': (
    <>
      이 서비스는 공공데이터포털의 목록 정보와 일부 실제 파일에서 확인한 구조 정보를
      바탕으로 합니다. 실제 데이터의 내용과 품질, 다른 데이터와 함께 사용할 수 있는지는
      보증하지 않습니다. 모든 데이터의 이용(다운로드·활용신청)은{' '}
      <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">공공데이터포털</a>에서
      가능합니다.
    </>
  ),
  // 영어 표면에서만 뜨는 '데이터는 번역되지 않는다' 고지 — 한국어에서는 불필요(빈 문자열이면 렌더 생략)
  'app.dataLangNote': '',
  'app.footerChanges': '변경 이력',
  'app.footerPrivacy': '개인정보·로그 안내',

  // ---- 검색(SearchView)
  'search.examples': [
    { q: '어린이 보호구역', label: '어린이 보호구역' },
    { q: '산후조리원 현황', label: '산후조리원 현황' },
    { q: '무더위 쉼터', label: '무더위 쉼터' },
    { q: '식품 제조 공장', label: '식품 제조 공장' },
    { q: '버스 정류장 위치', label: '버스 정류장 위치' },
    { q: '관광지 방문객', label: '관광지 방문객' },
  ],
  'search.columnExamples': [
    { q: '위도, 경도', label: '위도, 경도' },
    { q: '주소, 전화번호', label: '주소, 전화번호' },
    { q: '사업자등록번호', label: '사업자등록번호' },
    { q: '설치연도', label: '설치연도' },
  ],
  'search.purposeExamples': [
    { q: '전기차 충전소 위치와 운영기관을 분석하고 싶다', label: '전기차 충전소 위치와 운영기관을 분석하고 싶다' },
    { q: '고령자 의료 접근성을 지역별로 비교하고 싶다', label: '고령자 의료 접근성을 지역별로 비교하고 싶다' },
    { q: '어린이 보호구역 교통안전을 분석하고 싶다', label: '어린이 보호구역 교통안전을 분석하고 싶다' },
  ],
  'search.heroTitle': '어떤 데이터를 찾고 계신가요?',
  'search.heroSub': '공공데이터를 찾고, 이해하고, 활용하는 데 필요한 근거를 제공합니다.',
  'search.modeAria': '탐색 방식',
  'search.modeKeyword': '키워드',
  'search.modeColumns': '컬럼',
  'search.modeColumnsTitle': '실제 파일에서 관측된 원본 컬럼명으로 데이터셋을 찾습니다',
  'search.modePurpose': '목적',
  'search.modePurposeTitle': '데이터 이름을 몰라도 하려는 일을 적으면 후보와 한계를 초안으로 조립합니다',
  'search.phKeyword': '데이터명·기관명 — 예: 전기차 충전소',
  'search.phColumns': '필요한 컬럼 — 예: 사업자등록번호, 업종',
  'search.phPurpose': '하려는 일 — 예: 폐교 활용 사업 검토',
  'search.submit': '검색',
  'search.submitPlan': '초안 조립',
  'search.hintColumns':
    '실제 파일에서 관측된 원본 컬럼명과 부분 일치하는 데이터셋을 찾습니다 — 여러 개를 쉼표로 적으면 모두 가진 것만(AND) 반환합니다.',
  'search.hintPurpose':
    '결정론 규칙(plan-assembly-v1.0)이 목적을 해석해 후보·역할·한계를 조립합니다 — LLM 없음, 판정 없음, 결과는 항상 초안(DRAFT)입니다.',
  // 한국어 카탈로그 안내 — 한국어 표면에서는 불필요
  'search.hintLang': '',
  'search.interpMark': '해석',
  'search.interpApplied': ({ filters }) => (
    <>검색어에서 <strong>{filters}</strong> 조건을 읽어 적용했습니다</>
  ),
  'search.interpDismiss': '원문 그대로 검색',
  'search.examplesLabel': '예:',
  'search.browseAll': '데이터 목록 둘러보기 →',
  'search.rankingTitle': '랭킹 {method} ({version})',
  'search.total': '총 {n}건',
  'search.byRelevance': ' · 관련도순(제목·키워드·설명·제공 기관 기준)',
  'search.byModified': ' · 최근 수정순',
  'search.topShown': ' · 상위 {n}건 표시 — 컬럼 검색에는 커서 페이징이 없습니다(컬럼을 추가해 좁혀 보세요)',
  'search.sortAria': '정렬',
  'search.sortRelevance': '관련도순',
  'search.sortModified': '최근 수정순',
  'search.chipRemove': '조건 해제',
  'search.filters': '필터',
  'search.typeAll': '유형 전체',
  'search.typeStd': '표준(STD)',
  'search.includeInferred': '추론 지역 포함',
  'search.cycleAll': '주기 전체',
  'search.formatAll': '포맷 전체',
  'search.assembling': '초안 조립 중…',
  'search.emptyTitle': '이 조건으로는 결과가 없습니다',
  'search.emptyScope': '조회 범위: {snapshot} 스냅샷',
  'search.emptyColumns':
    ' — 컬럼 검색은 구조가 관측된 {n}건 안에서만 찾습니다. 결과에 없다고 해당 컬럼이 없는 것이 아닙니다(미수집일 수 있음).',
  'search.emptyAll': ' 전체 목록.',
  'search.emptyAdvice': (
    <>
      키워드를 줄이거나 필터를 해제해 보세요. 찾는 방식이 막막하면 우측 상단
      <strong> AI에 연결</strong>로 대화하며 탐색할 수도 있습니다.
    </>
  ),
  'search.more': '결과 더 보기',

  // ---- 구조 수집 상태(CoverageIndicator)
  'cov.chipTitle': '구조 수집 상태: {label}',
  'cov.filesObserved': ' · 파일 {a}/{b}개 관측',
  'cov.examplesWithheld': ' · 예시값 비공개(법적 확인 전)',
  'cov.population': ({ searched, total }) =>
    `구조가 관측된 ${searched}건${total != null ? ` (전체 파일 목록 ${total}건)` : ''} 중 검색`,

  // ---- 결과 행(DatasetRow)
  'row.completenessTitle': ({ filled, total, profile, rule, typical, share, top }) =>
    `메타데이터 ${filled}/${total} 항목 기재 (${profile} 프로파일, ${rule})`
    + (typical ? ` — 동일 유형의 ${share}%가 같은 수준` : ` — 상위 ${top}%`),
  'row.filled': '메타데이터 {total}개 항목 중 {filled}개 기재',
  'row.typical': ' · 기재 수준: 표준',
  'row.topPercent': ' · 같은 유형 중 상위 {p}%',
  'row.rows': '{n}행',
  'row.matchedColumns': '일치 컬럼: ',
  'row.matchedFields': '검색어가 일치한 항목: ',
  'row.compareTitle': '비교에 추가 (최대 5개)',
  'row.compare': '비교하기',
  'row.portal': '포털 원문 보기 ↗',

  // ---- 근거 표기(EvidenceRow)
  'ev.regionTitle': '{label} · 신뢰도 {conf}',
  'ev.inferredMark': '지역 정보 추론',
  'ev.level': '확인 근거: {label}({level})',
  'ev.observation': '관측 {date} · {prov} · 스캔 {scope}',
  'ev.snapshot': '판정 스냅샷 {s}',
  'ev.rules': '규칙 {r}',

  // ---- 데이터셋 상세(DatasetProfile)
  'profile.aria': '{title} 상세',
  'profile.ariaFallback': '데이터셋 상세',
  'profile.lensAria': '상세 렌즈',
  'profile.portalTab': '포털 원문 ↗',
  'profile.close': '상세 닫기',
  'profile.meta': "판정 스냅샷 {s} — 상세 근거는 '근거' 렌즈에서",
  'profile.k.theme': '분류',
  'profile.k.formats': '제공 형식',
  'profile.k.cycle': '갱신 주기',
  'profile.k.license': '이용 조건',
  'profile.k.created': '등록일',
  'profile.k.modified': '수정일',
  'profile.k.spatial': '공간 범위',
  'profile.k.temporal': '시간 범위',
  'profile.k.rows': '전체 행',
  'profile.k.apiType': 'API 유형',
  'profile.notListed': '목록에 기재되지 않음',
  'profile.completenessTitle': '{profile} 프로파일 · {rule}',
  'profile.filled': '메타데이터 {total}개 항목 중 {filled}개 기재',
  'profile.filledDetail': ({ profile, typical, share, top }) =>
    ` (${profile} 유형 · ${typical ? `같은 유형의 ${share}%가 동일한 기재 수준` : `같은 유형 중 상위 ${top}%`})`,
  'profile.ageDays': ' · 수정 후 {n}일',
  'profile.descTitle': '데이터 설명',
  'profile.descSrc': '(제공 기관 원문)',
  'profile.limitsTitle': '데이터 한계 (기관 기재)',
  'profile.keywordsLabel': '제공 기관이 등록한 키워드',
  'profile.portalBox': ({ listKey, org, base, analyzed }) => (
    <>
      목록 ID <code>{listKey}</code> · 제공 기관 {org} · 목록 스냅샷 {base} · 분석 기준일 {analyzed}
    </>
  ),
  'profile.portalLink': '공공데이터포털에서 원문 확인 ↗',
  'profile.evTitle': '근거 — 이 카드의 판정이 어디서 왔는가',
  'profile.k.snapshot': '판정 스냅샷',
  'profile.snapshotV': '{s} (처리 {p})',
  'profile.k.schema': '스키마 버전',
  'profile.freshNote': '최신성 주석: {note}',
  'profile.rulesSummary': '판정 방식 — 적용 규칙 버전 보기',
  'profile.k.rules': '적용 규칙',
  'profile.k.cardRule': '카드 재구성 규칙',
  'profile.k.completenessRule': '완전성 규칙',
  'profile.completenessRuleV': '{rule} ({profile} 프로파일)',
  'profile.k.freshRule': '최신성 규칙',
  'profile.regionTitle': '지역 판정',
  'profile.regionItem': ({ name, label, code, conf }) => (
    <>{name} — {label}(<code>{code}</code>) · 신뢰도 {conf}</>
  ),
  'profile.provNote':
    "구조 관측의 출처(provenance·스캔 범위)는 '데이터 구조' 렌즈의 파일별 관측 정보에 있습니다.",
  'profile.rawTitle': '원본 데이터 — 기술 표현',
  'profile.failReason': '실패 사유: {r}',
  'profile.licenseGate': ' · 예시값 라이선스 보류',
  'profile.sheet': '시트: {s}',
  'profile.th.source': '원본 컬럼명',
  'profile.th.type': '관측 유형',
  'profile.th.distinct': '고유값',
  'profile.th.examples': '예시값',
  'profile.tableMeta': ({ scanned, observed, cols, scope }) =>
    `스캔 행 ${scanned}${observed != null ? ` / 관측된 전체 행 ${observed}` : ''} · 컬럼 ${cols} · 범위 ${scope}`,

  // ---- 둘러보기 블록(HomeBlocks·ExploreView)
  // 서사 블록의 목적 문장 — /api/plan에 보내는 질의(q)는 한국어 카탈로그 기준으로 고정
  'home.storyPurpose': { q: '어린이 보호구역 교통안전을 분석하고 싶다', label: '어린이 보호구역 교통안전을 분석하고 싶다' },
  'home.storyTitle': '이렇게 탐색합니다',
  'home.step1': ({ terms, region }) => (
    <>
      <strong>목적 파악</strong> — 질문에서 {terms}을 핵심어로 찾습니다
      {region && <> · 지역 {region}(문장에서 추출)</>}
    </>
  ),
  'home.step2': ({ titles }) => <><strong>후보 찾기</strong> — {titles}</>,
  'home.step3': (
    <>
      <strong>예상 역할과 선정 근거</strong> — 각 데이터가 분석에서 어떤 역할을 할 수
      있는지와 후보로 선정된 근거를 보여줍니다. 여러 정보를 하나의 점수로 합쳐 순위를
      매기지는 않습니다.
    </>
  ),
  'home.step4': ({ check }) => <><strong>한계 확인</strong> — {check}</>,
  'home.storyNote': (
    <>
      이 결과는 생성형 AI가 작성한 답변이 아닙니다. 정해진 규칙(<code>plan-assembly-v1.0</code>)에
      따라 만들어지며, 같은 데이터와 같은 입력에는 같은 결과를 제공합니다. 데이터 품질을
      판정한 결과가 아니므로(<code>NOT_ASSESSED</code>), 실제 활용 전에 검토가 필요한
      초안(<code>DRAFT</code>)입니다.
    </>
  ),
  'home.storyCta': '내 목적에 맞는 데이터 찾기 →',
  'home.anatomyTitle': '데이터셋은 이렇게 읽힙니다',
  'home.anatomyCta': '전체 구조·근거 보기 →',
  'home.covTitle': '구조 관측 커버리지',
  'home.covAll': '목록 전체',
  'home.covFile': 'FILE 유형',
  'home.covObserved': '구조 관측 확보',
  'home.covNote':
    '구조 관측 확보분은 FILE의 {pf}% · 전체의 {pa}%입니다. API·STD 유형은 아직 구조 관측 대상이 아닙니다(API_STRUCTURE_NOT_SUPPORTED_YET).',
  'home.covLag': ({ snapshot, deployed, lag, release }) => (
    <>
      현재 스냅샷 {snapshot} · 배포 {deployed}
      {lag != null && <> — 스냅샷 기준월 시작으로부터 {lag}일 지연</>}
      {' '}· 릴리스 <code>{release}</code>
    </>
  ),
  'home.infraTitle': '공개된 검색·비교 기준 — {n}개 규칙',
  'home.infraSub':
    '데이터를 찾고 비교할 때 적용하는 {n}개 규칙을 공개하고 있습니다. 각 결과에는 적용한 규칙과 버전이 기록되므로, 어떤 기준으로 결과가 만들어졌는지 확인하고 다시 검증할 수 있습니다.',
  'home.deprecated': ' 폐기',
  'home.effective': '시행일 {d}',
  'home.evalMetrics': '검색 성능 참고값({q}개 검색 질문으로 측정): P@10 {p} · R@10 {r} · nDCG@10 {n}',
  'home.evalUnreviewed': ' — 질문은 자동 생성되었으며 아직 사람이 검토하지 않은 결과입니다',
  'home.evalFull': '전체 리포트',
  'home.techDocs': '기술 자료:',
  'home.linkRules': '규칙 레지스트리',
  'home.linkSchema': '도구 스키마',
  'home.linkContext': 'JSON-LD Context',
  'home.linkShapes': 'SHACL',
  'home.linkPrompt': '예시 프롬프트',
  'home.linkPrivacy': '개인정보·로그 안내',
  'explore.title': '둘러보기 — 이 서비스는 데이터를 이렇게 읽습니다',
  'explore.intro':
    '데이터 제목만 검색하지 않습니다. 데이터의 구조와 선정 근거, 활용할 때 확인해야 할 한계까지 함께 살펴봅니다. 아래 예시는 현재 서비스에 반영된 공공데이터포털의 실제 목록을 바탕으로 합니다.',
  'explore.liveTitle': '구조를 바로 확인할 수 있는 데이터 — 최근 수정된 데이터 중 3건',

  // ---- 관측 현황(ObservatoryView)
  'obs.unspecified': '(미기재)',
  'obs.count': '{n}건',
  'obs.loadFail': '관측 현황을 불러오지 못했습니다.',
  'obs.title': '관측 현황',
  'obs.titleSnapshot': ' — {s} 스냅샷',
  'obs.intro':
    '이 페이지는 현재 스냅샷에서 확인된 사실을 보여줍니다. 평가하거나 순위를 매기는 것이 아니라, 무엇을 확인했고 무엇을 아직 확인하지 못했는지를 구분합니다. 모든 수치에는 적용한 규칙과 버전이 기록됩니다.',
  'obs.sizeTitle': '데이터 규모와 제공 유형',
  'obs.sizeIntro': '공공데이터포털의 목록 {n}건이 반영되어 있습니다.',
  'obs.typeFail': '유형 분포를 불러오지 못했습니다.',
  'obs.structTitle': '실제 파일 구조 확인 현황',
  'obs.structFigure': ({ total, n }) => (
    <>파일로 제공되는 {total}건 가운데 <strong>{n}건</strong>은 실제 컬럼 구조를 확인했습니다.</>
  ),
  'obs.structNote': '아직 확인하지 못한 목록은 수집 대기 상태입니다. 데이터 품질이 낮다는 뜻은 아닙니다.',
  'obs.structUnavailable': '현재 서비스 버전에서는 실제 파일 구조를 확인한 범위를 제공하지 않습니다.',
  'obs.complTitle': '목록 정보 기재 현황 — 제공 유형별',
  'obs.complIntro':
    '파일·API·표준데이터는 확인하는 항목 수가 서로 다릅니다. 따라서 같은 유형 안에서만 산출하며, 유형 간 수치를 합치거나 직접 비교하지 않습니다.',
  'obs.avgRate': '평균 기재율 {p}%',
  'obs.noTarget': '산출 대상 없음',
  'obs.complFail': '완전성 분포를 불러오지 못했습니다.',
  'obs.themeTitle': '주제별 분포 — 목록 수 상위 {n}개',
  'obs.themeFail': '주제 분포를 불러오지 못했습니다.',
  'obs.orgTitle': '제공 기관별 분포 — 목록 수 상위 {n}개 기관',
  'obs.orgNote': '목록 수는 기관의 데이터 개방 규모를 보여줄 뿐, 데이터 품질 순위는 아닙니다.',
  'obs.orgFail': '기관 분포를 불러오지 못했습니다.',
  'obs.familyTitle': '같은 계열로 보이는 데이터',
  'obs.familyFail': '계열 통계를 불러오지 못했습니다.',
  'obs.familyUnavailable':
    '현재 서비스 버전에서는 같은 계열로 보이는 데이터 후보를 아직 산출하지 않았습니다. 후보가 0건이라는 뜻은 아닙니다.',
  'obs.familyFigure': '같은 계열로 보이는 후보 묶음 {f}개(목록 {m}건)를 자동으로 찾았습니다.',
  'obs.familyNote': '자동으로 찾은 후보이며, 같은 계열로 확정한 것은 아닙니다. ',
  'obs.familyStatus': '{label} {n}건',
  'obs.changesTitle': '월별 변경 현황',
  'obs.changesFail': '변경 통계를 불러오지 못했습니다.',
  'obs.changesAccumulating':
    '월간 스냅샷이 두 개 이상 쌓이면 신규·변경·미관측 통계를 제공합니다. 현재는 첫 스냅샷을 축적하는 단계입니다.',
  'obs.changesFigure': '{base}부터 {cur}까지 확인된 변경입니다.',
  'obs.changesNote':
    '‘스냅샷에서 확인되지 않음(MISSING_FROM_SNAPSHOT)’은 데이터가 폐기되었다는 뜻이 아닙니다. 공식적으로 폐기된 경우에만 ‘공식 폐기(OFFICIALLY_WITHDRAWN)’로 표시합니다.',

  // ---- 소개(AboutView)
  'about.heroTitle': '하고 싶은 일을 말하면, 근거와 함께 공공데이터를 찾아드립니다',
  'about.heroBody': (
    <>
      공공데이터 렌즈는 <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">공공데이터포털</a>에
      등록된 약 9만 6천 건의 데이터를 목적에 맞게 찾고 비교하는 서비스입니다. 데이터가
      검색된 이유와 확인된 정보의 범위를 함께 보여주어, 어떤 데이터를 먼저 검토해야 할지
      판단할 수 있게 합니다. 검색과 비교 결과는 공개된 기준에 따라 만들어집니다. 같은
      데이터와 같은 조건에는 같은 결과가 나오며, 적용된 기준과 버전도 확인할 수 있습니다.
      다만 이 서비스의 결과가 실제 데이터의 내용이나 품질을 보증하는 것은 아닙니다.
      데이터 이용과 원문 확인은 공공데이터포털에서 이루어집니다.
    </>
  ),
  'about.research': (
    <>
      <a href="http://hike.cau.ac.kr" target="_blank" rel="noreferrer">중앙대학교 HIKE 연구실</a>이
      운영하며, 현재 제정 중인 AI Ready Data 표준안(정보통신단체표준)에 앞서 개발된
      독립 구현으로, 표준안의 실현 가능성을 실제 공공데이터로 검증하는 프로젝트이기도
      합니다.
    </>
  ),
  'about.catalogTitle': '카탈로그 현황',
  'about.statAll': '전체 목록 수',
  'about.statStruct': '실파일 구조 확인',
  'about.statSnapshot': '현재 스냅샷(매월 갱신)',
  'about.statAnalyzed': '분석 기준일',
  'about.loading': '현황을 불러오는 중…',
  'about.principlesTitle': '데이터 출처와 운영 원칙',
  'about.principles': [
    <>공공데이터포털이 매월 공개하는 <a href="https://www.data.go.kr/data/15062804/fileData.do" target="_blank" rel="noreferrer">데이터 목록</a>을 바탕으로 정보를 갱신합니다. 실제 데이터를 대신 배포하지 않으며, 데이터 이용과 원문 확인은 공공데이터포털에서 이루어집니다.</>,
    <>목록에 등록된 설명과 실제 파일에서 확인한 구조는 구분합니다. 실제 파일을 확인하지 못하면 확인되지 않았다는 사실도 함께 표시합니다. 화면에서는 각각 목록 정보 기준(<code>CATALOG_METADATA_ONLY</code>)과 실제 파일 확인(<code>FILE_OBSERVATION</code>)으로 구분합니다.</>,
    <>서비스 이용 기록에는 접속자의 IP 주소를 저장하지 않습니다. 브라우저의 DNT 또는 GPC 설정을 통해 수집을 거부할 수 있습니다. <a href="/api/resources/privacy" target="_blank" rel="noreferrer">개인정보·로그 안내</a></>,
    <>목록 정보에서 오류가 의심되는 경우 <a href="https://github.com/hike-lab/public-data-lens/issues" target="_blank" rel="noreferrer">GitHub Issues</a>를 통해 알려주세요. 확인한 내용은 필요한 경우 데이터 제공 기관에 전달합니다.</>,
  ],

  // ---- MCP 연결(ConnectView)
  'connect.heroTitle': '웹에서 제공하는 데이터 탐색 기능을 AI에서도 사용할 수 있습니다',
  'connect.heroBody': (
    <>
      공공데이터 렌즈의 검색·비교·구조 확인 기능은 <strong>MCP(Model Context Protocol)</strong>
      서버로도 제공됩니다. MCP를 지원하는 AI에 아래 주소를 등록하면 대화로 데이터를
      탐색할 수 있습니다. 인증 없이 무료로 이용할 수 있으며, 웹과 같은 기준을 사용하므로
      확인 근거와 적용한 규칙 버전도 함께 표시됩니다.
    </>
  ),
  'connect.copy': '복사',
  'connect.copied': '복사됨 ✓',
  'connect.capTitle': '연결하면 이렇게 이용할 수 있습니다',
  'connect.capAsk': '말로 요청하기',
  'connect.capQuote': '“전기차 충전소 중 위도·경도가 실제로 있고, 지역별 비교에 쓸 만한 데이터를 찾아줘”',
  'connect.capSteps': '렌즈가 단계별로 탐색하기',
  'connect.step1': '목적 파악',
  'connect.step2': '필요한 컬럼 검색',
  'connect.step3': '후보 비교',
  'connect.step4': '실제 구조 확인',
  'connect.capOut': '근거와 함께 결과 확인하기',
  'connect.out1': '후보 데이터와 예상 역할 — 확정된 결과가 아니라 먼저 검토할 대상입니다',
  'connect.out2': <>좌표 컬럼을 실제 파일에서 확인한 근거(<code>FILE_OBSERVATION</code>)</>,
  'connect.out3': <>한계와 확인하지 못한 항목(<code>NOT_ASSESSED</code>·<code>CANDIDATE_ONLY</code>)</>,
  'connect.out4': '적용한 규칙 버전과 데이터 스냅샷',
  'connect.howTitle': 'AI 서비스별 연결 방법',
  'connect.claudeWeb': 'Claude 웹·앱',
  'connect.claudeSteps': [
    <>웹(claude.ai)에서 <strong>설정 → 커넥터 → 커스텀 커넥터 추가</strong></>,
    <>위 주소를 붙여넣고 추가</>,
    <>대화에서 바로 질문 — 정형화된 활용 계획은 프롬프트 메뉴의 <code>build_data_plan</code></>,
    <>연결을 확인하려면 이렇게 물어보세요: “이 커넥터로 공공데이터 카탈로그 현황을 알려줘”</>,
  ],
  'connect.claudeCaveat': (
    <>
      Team·Enterprise 계정에서는 구성원 설정에 커넥터 추가 메뉴가 보이지 않을 수
      있습니다. 이 경우 조직 관리자가 먼저 커넥터를 추가해야 하며, 구성원은
      <strong>설정 → 커넥터</strong>에서 ‘연결’을 눌러 활성화할 수 있습니다. 데스크톱
      앱에서는 아래 안내에 따라 Claude Code에 등록한 뒤
      <strong> 설정 → 커넥터</strong>에서 활성화할 수도 있습니다.
    </>
  ),
  'connect.claudePermission': (
    <>
      처음 사용할 때 Claude가 도구 호출마다 허용 여부를 묻는 것은 정상입니다.
      허용 창에서 <strong>‘항상 허용’</strong>을 선택하면 이후에는 다시 묻지 않습니다.
      이 서버의 도구는 모두 읽기 전용으로, 데이터를 추가·수정·삭제하지 않습니다.
    </>
  ),
  'connect.claudeCode': 'Claude Code(터미널)',
  'connect.claudeCodeCheck': <>연결 확인: <code>claude mcp list</code>에서 connected 표시</>,
  'connect.chatgpt': 'ChatGPT 웹',
  'connect.chatgptStep1': <><strong>설정 → 보안 및 로그인 → 개발자 모드</strong> 켜기</>,
  'connect.chatgptStep2': <><a href="https://chatgpt.com/plugins" target="_blank" rel="noreferrer">ChatGPT Plugins</a> → <code>+</code> 선택</>,
  'connect.chatgptStep3': '다음 정보로 MCP 앱 등록:',
  'connect.chatgptTable': ({ mcpUrl }) => [
    ['이름', '공공데이터 렌즈'],
    ['설명', '한국 공공데이터를 목적·키워드·컬럼 기준으로 검색하고 구조와 근거를 확인합니다.'],
    ['연결', 'Public endpoint'],
    ['MCP 서버 URL', <code>{mcpUrl}</code>],
    ['인증', 'No Authentication'],
  ],
  'connect.chatgptStep4': '생성 후 탐지된 도구 목록 확인',
  'connect.chatgptStep5': <>새 대화 → 입력창의 <code>+</code> → 개발자 모드 → 공공데이터 렌즈 선택</>,
  'connect.chatgptStep6': '대화에서 바로 질문',
  'connect.chatgptCheck': (
    <>
      연결 확인: "공공데이터 렌즈를 사용해서 공공데이터 카탈로그 현황을 알려줘."<br />
      활용 계획 작성: "공공데이터 렌즈를 사용해서 전기차 충전소 분석에 필요한 데이터
      활용 계획을 만들어줘."
    </>
  ),
  'connect.chatgptCaveat':
    '개발자 모드는 현재 ChatGPT 웹의 Plus·Pro·Business·Enterprise·Education 계정에서 제공되며, 조직 계정은 관리자 정책에 따라 제한될 수 있습니다.',
  'connect.other': '기타 MCP 클라이언트',
  'connect.otherBody': (
    <>
      원격 MCP(streamable HTTP)를 지원하는 클라이언트라면 같은 주소로 등록할 수 있습니다.
      명세: <a href="/projects/public-data-lens/spec/tools/1.0" target="_blank" rel="noreferrer">Tool 스키마(JSON)</a>
    </>
  ),
  'connect.reconnect': (
    <>
      <strong>새로 추가된 기능이 보이지 않으면</strong> 커넥터를 한 번 다시 연결해 주세요.
      AI 앱은 연결한 시점의 기능 목록을 기억하기 때문에, 그 뒤에 추가된 기능은
      재연결 후에 나타납니다. 데이터 갱신은 재연결 없이 바로 반영됩니다.
    </>
  ),
  'connect.askTitle': '이렇게 물어보세요',
  'connect.examplePrompts': [
    '폐교 활용 사업을 검토 중인데 참고할 공공데이터 찾아줘',
    '고령자 의료 접근성 분석에 쓸 데이터 후보를 비교해줘',
    '위도·경도 컬럼이 실제로 있는 관광 데이터만 골라줘',
  ],
  'connect.featuresTitle': '제공 기능',
  'connect.featuresBody': (
    <>
      데이터셋 검색 · 상세 조회 · 최대 5개 비교 · 월별 변경 확인 · 카탈로그 통계 ·
      컬럼 기준 검색 · 실제 파일 구조 확인 · <strong>데이터 활용 계획 초안(build_data_plan)</strong> ·
      서비스 안내 — 총 9개입니다. 하고 싶은 일을 한 문장으로 입력하면 후보 데이터의
      역할과 선정 근거, 연결에 사용할 것으로 예상되는 항목, 활용 전에 확인할 한계가
      포함된 계획 초안을 받을 수 있습니다. 각 결과에는 확인 근거와 적용한 규칙 버전이
      표시됩니다.
    </>
  ),

  // ---- 비교(CompareView)
  'compare.emptyHint': '검색 탭에서 데이터셋을 2~5개 선택하면 구조화된 사실 비교를 보여줍니다.',
  'compare.oneSelected': '현재 1개 선택됨 — 1개 더 선택하세요.',
  'compare.loading': '비교 중…',
  'compare.thField': '항목',
  'compare.remove': '제외',
  'compare.shared': ' (공통)',
  'compare.sharedHide': '공통 항목 접기',
  'compare.sharedShow': '공통 항목 {n}개 보기',
  'compare.structTitle': '원본 컬럼 구조 비교',
  'compare.common': '공통 컬럼 {n}개:',
  'compare.none': '없음',
  'compare.onlyIn': '{title}에만:',
  'compare.totalCols': ' (전체 {n}개)',

  // ---- 변경 이력(ChangesView)
  'changes.all': '전체',
  'changes.base': '비교 기준: {b} → {c}',
  'changes.summary': '이번 스냅샷에서 확인된 변경: ',
  'changes.count': '{label} {n}건',
  'changes.empty': '해당 상태의 변경이 없습니다.',
  'changes.fields': '변경 필드: {f}',
  'changes.more': '더 보기',

  // ---- 활용 계획(PossibleUsesLens·PlanResult)
  'plan.status': ({ status }) => <>계획 상태: 초안(<code>{status}</code>)</>,
  'plan.quality': ({ q }) => <>품질: 미평가(<code>{q}</code>)</>,
  'plan.interpretedTitle': '해석된 목적',
  'plan.terms': '검색어 {t}',
  'plan.region': ({ r, fromParam }) => ` · 지역 ${r} (${fromParam ? '지정' : '문장에서 추출'})`,
  'plan.iterations': ' · 검색 반복 {n}회',
  'plan.needsTitle': '데이터 요구',
  'plan.candidatesTitle': '후보 데이터셋 (근거는 목록·관측 사실)',
  'plan.joinTitle': '예상 결합 키 — 전부 후보(CANDIDATE_ONLY)',
  'plan.joinEmpty': '관측 근거가 있는 결합 키 후보가 없습니다 — 원문 컬럼 정의에서 직접 확인이 필요합니다.',
  'plan.missingTitle': '미충족 요구',
  'plan.nextTitle': '다음 확인사항',
  'plan.lensTitle': '활용 계획 초안',
  'plan.lensIntro':
    '하고 싶은 일을 한 문장으로 적으면 결정론 규칙(plan-assembly-v1.0)이 후보와 한계를 조립합니다 — LLM 없음, 판정 없음, 항상 초안입니다.',
  'plan.placeholder': ({ title }) => `예: ${title ? `${title.slice(0, 24)}로 ` : ''}지역 간 격차를 분석하고 싶다`,
  'plan.purposeAria': '활용 목적',
  'plan.submit': '초안 조립',
  'plan.assembling': '조립 중…',
}
