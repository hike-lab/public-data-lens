// Interface strings — English. Key set must match strings.ko.jsx (enforced by i18n.test.js).
// Values: string ('{name}' placeholders), function (word order / conditionals / JSX), array or object.
// Server-provided values are never translated here: dataset titles, publishers, descriptions,
// warnings[], rule definitions and region names render verbatim in both languages (invariants 3·4).
// Example search queries (q) are identical to Korean because they query a Korean-language catalog;
// only the visible label carries an English gloss.
// Vocabulary follows DESIGN.md §8 — candidate, observed, confirmed, metadata, file observation,
// additional verification required. Avoid: recommended, guaranteed, AI-ready, suitable, complete, best.

export const STRINGS_EN = {
  // ---- common
  'common.loading': 'Loading…',

  // ---- language switch
  'lang.aria': 'Display language',
  'lang.ko': '한국어',
  'lang.en': 'English',

  // ---- App (top nav · footer · compare bar)
  'nav.concierge': 'AI Concierge',
  'nav.explore': 'Explore',
  'nav.observatory': 'Observations',
  'nav.about': 'About',
  'nav.connect': 'Connect via MCP',
  'app.brandHome': 'Public Data Lens home',
  'app.navAria': 'Secondary menu',
  'app.backToSearch': '← Back to search',
  'app.selectedCount': '{n} selected',
  'app.compareGo': 'Compare →',
  'app.compareClear': 'Clear',
  'app.conciergeOpen': 'Open AI Concierge',
  'app.footerDisclaimer': (
    <>
      This service is based on catalog listings from the Korean Public Data Portal and on
      structure observed in a subset of actual files. It does not vouch for the content or
      quality of the data, nor for whether datasets can be combined. All data access
      (downloads and usage requests) happens on the{' '}
      <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">Public Data Portal</a>.
    </>
  ),
  'app.dataLangNote':
    'English applies to the interface only. Dataset titles, publishers, descriptions and server notices are shown as published, in Korean.',
  'app.footerChanges': 'Change log',
  'app.footerPrivacy': 'Privacy & logging notice',

  // ---- Search (SearchView) — queries stay Korean; labels carry a gloss
  'search.examples': [
    { q: '어린이 보호구역', label: '어린이 보호구역 · school zones' },
    { q: '산후조리원 현황', label: '산후조리원 현황 · postnatal care centres' },
    { q: '무더위 쉼터', label: '무더위 쉼터 · heat-wave shelters' },
    { q: '식품 제조 공장', label: '식품 제조 공장 · food factories' },
    { q: '버스 정류장 위치', label: '버스 정류장 위치 · bus stop locations' },
    { q: '관광지 방문객', label: '관광지 방문객 · tourist visitors' },
  ],
  'search.columnExamples': [
    { q: '위도, 경도', label: '위도, 경도 · latitude, longitude' },
    { q: '주소, 전화번호', label: '주소, 전화번호 · address, phone' },
    { q: '사업자등록번호', label: '사업자등록번호 · business registration no.' },
    { q: '설치연도', label: '설치연도 · year installed' },
  ],
  'search.purposeExamples': [
    { q: '전기차 충전소 위치와 운영기관을 분석하고 싶다', label: 'EV charging station locations and operators (전기차 충전소 위치와 운영기관을 분석하고 싶다)' },
    { q: '고령자 의료 접근성을 지역별로 비교하고 싶다', label: 'Compare healthcare access for older adults by region (고령자 의료 접근성을 지역별로 비교하고 싶다)' },
    { q: '어린이 보호구역 교통안전을 분석하고 싶다', label: 'Analyse traffic safety in school zones (어린이 보호구역 교통안전을 분석하고 싶다)' },
  ],
  'search.heroTitle': 'What data are you looking for?',
  'search.heroSub': 'Evidence for finding, understanding and using Korean public data.',
  'search.modeAria': 'Search mode',
  'search.modeKeyword': 'Keyword',
  'search.modeColumns': 'Columns',
  'search.modeColumnsTitle': 'Find datasets by column names observed in the actual files',
  'search.modePurpose': 'Purpose',
  'search.modePurposeTitle': 'Describe what you want to do; candidates and limits are assembled as a draft, even if you do not know dataset names',
  'search.phKeyword': 'Dataset or publisher (Korean) — e.g. 전기차 충전소',
  'search.phColumns': 'Columns (Korean) — e.g. 사업자등록번호, 업종',
  'search.phPurpose': 'Your goal (Korean) — e.g. 폐교 활용 사업 검토',
  'search.submit': 'Search',
  'search.submitPlan': 'Assemble draft',
  'search.hintColumns':
    'Finds datasets whose column names, as observed in the actual files, partially match. Separate several with commas to return only datasets that have all of them (AND).',
  'search.hintPurpose':
    'A deterministic rule (plan-assembly-v1.0) interprets the purpose and assembles candidates, roles and limits — no LLM, no verdict, and the result is always a DRAFT.',
  'search.hintLang':
    'The catalog is in Korean. Keywords, column names and purpose sentences match most reliably when written in Korean.',
  'search.interpMark': 'Interpreted',
  'search.interpApplied': ({ filters }) => (
    <>Read <strong>{filters}</strong> from your query and applied it as a filter</>
  ),
  'search.interpDismiss': 'Search the text as is',
  'search.examplesLabel': 'Try:',
  'search.browseAll': 'Browse the dataset list →',
  'search.rankingTitle': 'Ranking {method} ({version})',
  'search.total': '{n} results',
  'search.byRelevance': ' · by relevance (title, keywords, description, publisher)',
  'search.byModified': ' · most recently modified first',
  'search.topShown': ' · showing the top {n} — column search has no cursor paging (add columns to narrow down)',
  'search.sortAria': 'Sort',
  'search.sortRelevance': 'Relevance',
  'search.sortModified': 'Recently modified',
  'search.chipRemove': 'Remove filter',
  'search.filters': 'Filters',
  'search.typeAll': 'All types',
  'search.typeStd': 'Standard (STD)',
  'search.includeInferred': 'Include inferred regions',
  'search.cycleAll': 'All cycles',
  'search.formatAll': 'All formats',
  'search.assembling': 'Assembling draft…',
  'search.emptyTitle': 'No results for these conditions',
  'search.emptyScope': 'Scope: the {snapshot} snapshot',
  'search.emptyColumns':
    ' — column search looks only within the {n} records whose structure has been observed. Absence from the results does not mean the column does not exist (it may simply not have been collected yet).',
  'search.emptyAll': ', full listing.',
  'search.emptyAdvice': (
    <>
      Try fewer keywords or remove a filter. Korean search terms match most reliably. If you are unsure how
      to search, you can also explore in conversation via <strong>Connect via MCP</strong> at the top right.
    </>
  ),
  'search.more': 'More results',

  // ---- structure collection status (CoverageIndicator)
  'cov.chipTitle': 'Structure collection status: {label}',
  'cov.filesObserved': ' · {a}/{b} files observed',
  'cov.examplesWithheld': ' · example values not shown (pending legal review)',
  'cov.population': ({ searched, total }) =>
    `Searched within ${searched} records with observed structure${total != null ? ` (of ${total} file listings)` : ''}`,

  // ---- result row (DatasetRow)
  'row.completenessTitle': ({ filled, total, profile, rule, typical, share, top }) =>
    `${filled}/${total} metadata fields filled (${profile} profile, ${rule})`
    + (typical ? ` — ${share}% of the same type are at this level` : ` — top ${top}% of the same type`),
  'row.filled': '{filled} of {total} metadata fields filled',
  'row.typical': ' · typical for its type',
  'row.topPercent': ' · top {p}% of its type',
  'row.rows': '{n} rows',
  'row.matchedColumns': 'Matching columns: ',
  'row.matchedFields': 'Query matched in: ',
  'row.compareTitle': 'Add to comparison (up to 5)',
  'row.compare': 'Compare',
  'row.portal': 'View on portal ↗',

  // ---- evidence (EvidenceRow)
  'ev.regionTitle': '{label} · confidence {conf}',
  'ev.inferredMark': 'region inferred',
  'ev.level': 'Evidence: {label} ({level})',
  'ev.observation': 'Observed {date} · {prov} · scan {scope}',
  'ev.snapshot': 'Snapshot {s}',
  'ev.rules': 'Rules {r}',

  // ---- dataset detail (DatasetProfile)
  'profile.aria': 'Details: {title}',
  'profile.ariaFallback': 'Dataset details',
  'profile.lensAria': 'Detail lenses',
  'profile.portalTab': 'Portal source ↗',
  'profile.close': 'Close details',
  'profile.meta': "Snapshot {s} — see the 'Evidence' lens for the full basis",
  'profile.k.theme': 'Category',
  'profile.k.formats': 'Formats',
  'profile.k.cycle': 'Update cycle',
  'profile.k.license': 'License',
  'profile.k.created': 'Registered',
  'profile.k.modified': 'Modified',
  'profile.k.spatial': 'Spatial coverage',
  'profile.k.temporal': 'Temporal coverage',
  'profile.k.rows': 'Total rows',
  'profile.k.apiType': 'API type',
  'profile.notListed': 'Not stated in the listing',
  'profile.completenessTitle': '{profile} profile · {rule}',
  'profile.filled': '{filled} of {total} metadata fields filled',
  'profile.filledDetail': ({ profile, typical, share, top }) =>
    ` (${profile} type · ${typical ? `${share}% of the same type are at this level` : `top ${top}% of the same type`})`,
  'profile.ageDays': ' · {n} days since modified',
  'profile.descTitle': 'Description',
  'profile.descSrc': '(publisher text, Korean)',
  'profile.limitsTitle': 'Data limits (stated by publisher)',
  'profile.keywordsLabel': 'Keywords registered by the publisher',
  'profile.portalBox': ({ listKey, org, base, analyzed }) => (
    <>
      Listing ID <code>{listKey}</code> · Publisher {org} · Listing snapshot {base} · Analysed {analyzed}
    </>
  ),
  'profile.portalLink': 'View the source on the Public Data Portal ↗',
  'profile.evTitle': 'Evidence — where the statements on this card come from',
  'profile.k.snapshot': 'Snapshot',
  'profile.snapshotV': '{s} (processed {p})',
  'profile.k.schema': 'Schema version',
  'profile.freshNote': 'Freshness note: {note}',
  'profile.rulesSummary': 'Method — show applied rule versions',
  'profile.k.rules': 'Applied rules',
  'profile.k.cardRule': 'Card assembly rule',
  'profile.k.completenessRule': 'Completeness rule',
  'profile.completenessRuleV': '{rule} ({profile} profile)',
  'profile.k.freshRule': 'Freshness rule',
  'profile.regionTitle': 'Region',
  'profile.regionItem': ({ name, label, code, conf }) => (
    <>{name} — {label} (<code>{code}</code>) · confidence {conf}</>
  ),
  'profile.provNote':
    "Provenance and scan scope of structure observations are listed per file in the 'Structure' lens.",
  'profile.rawTitle': 'Raw data — technical representations',
  'profile.failReason': 'Failure reason: {r}',
  'profile.licenseGate': ' · example values withheld (license)',
  'profile.sheet': 'Sheet: {s}',
  'profile.th.source': 'Source column name',
  'profile.th.type': 'Observed type',
  'profile.th.distinct': 'Distinct',
  'profile.th.examples': 'Examples',
  'profile.tableMeta': ({ scanned, observed, cols, scope }) =>
    `Rows scanned ${scanned}${observed != null ? ` / total rows observed ${observed}` : ''} · columns ${cols} · scope ${scope}`,

  // ---- explore blocks (HomeBlocks · ExploreView)
  'home.storyPurpose': { q: '어린이 보호구역 교통안전을 분석하고 싶다', label: 'I want to analyse traffic safety in school zones (어린이 보호구역 교통안전을 분석하고 싶다)' },
  'home.storyTitle': 'How exploration works here',
  'home.step1': ({ terms, region }) => (
    <>
      <strong>Interpret the purpose</strong> — {terms} are taken from the question as key terms
      {region && <> · region {region} (extracted from the sentence)</>}
    </>
  ),
  'home.step2': ({ titles }) => <><strong>Find candidates</strong> — {titles}</>,
  'home.step3': (
    <>
      <strong>Expected roles and selection basis</strong> — shows what role each dataset could
      play in the analysis and why it was selected as a candidate. Signals are not merged into a
      single score or ranking.
    </>
  ),
  'home.step4': ({ check }) => <><strong>Check the limits</strong> — {check}</>,
  'home.storyNote': (
    <>
      This is not an answer written by generative AI. It is produced by a fixed rule
      (<code>plan-assembly-v1.0</code>) and gives the same result for the same data and input.
      It is not a verdict on data quality (<code>NOT_ASSESSED</code>); it is a draft
      (<code>DRAFT</code>) to review before actual use.
    </>
  ),
  'home.storyCta': 'Find data for my own purpose →',
  'home.anatomyTitle': 'How a dataset is read',
  'home.anatomyCta': 'Full structure and evidence →',
  'home.covTitle': 'Structure observation coverage',
  'home.covAll': 'All listings',
  'home.covFile': 'FILE type',
  'home.covObserved': 'Structure observed',
  'home.covNote':
    'Structure has been observed for {pf}% of FILE listings · {pa}% of all listings. API and STD types are not yet observed for structure (API_STRUCTURE_NOT_SUPPORTED_YET).',
  'home.covLag': ({ snapshot, deployed, lag, release }) => (
    <>
      Current snapshot {snapshot} · deployed {deployed}
      {lag != null && <> — {lag} days after the start of the snapshot month</>}
      {' '}· release <code>{release}</code>
    </>
  ),
  'home.infraTitle': 'Published search and comparison rules — {n} rules',
  'home.infraSub':
    'The {n} rules applied when finding and comparing data are public. Every result records the rules and versions applied, so you can check how it was produced and verify it again.',
  'home.deprecated': ' deprecated',
  'home.effective': 'Effective {d}',
  'home.evalMetrics': 'Search quality reference ({q} evaluation queries): P@10 {p} · R@10 {r} · nDCG@10 {n}',
  'home.evalUnreviewed': ' — queries were generated automatically and have not yet been reviewed by a person',
  'home.evalFull': 'full report',
  'home.techDocs': 'Technical resources:',
  'home.linkRules': 'Rule registry',
  'home.linkSchema': 'Tool schemas',
  'home.linkContext': 'JSON-LD Context',
  'home.linkShapes': 'SHACL',
  'home.linkPrompt': 'Example prompt',
  'home.linkPrivacy': 'Privacy & logging notice',
  'explore.title': 'Explore — how this service reads data',
  'explore.intro':
    'We do not search titles alone. Structure, selection basis and the limits to check before use are examined together. The examples below use actual listings from the Public Data Portal as currently reflected in this service.',
  'explore.liveTitle': 'Datasets whose structure you can check right away — 3 of the most recently modified',

  // ---- observations (ObservatoryView)
  'obs.unspecified': '(not stated)',
  'obs.count': '{n}',
  'obs.loadFail': 'Could not load the observation summary.',
  'obs.title': 'Observations',
  'obs.titleSnapshot': ' — {s} snapshot',
  'obs.intro':
    'This page shows facts observed in the current snapshot. It does not evaluate or rank; it separates what has been confirmed from what has not yet been confirmed. Every figure records the rule and version applied.',
  'obs.sizeTitle': 'Catalog size and list types',
  'obs.sizeIntro': '{n} listings from the Public Data Portal are reflected.',
  'obs.typeFail': 'Could not load the list type distribution.',
  'obs.structTitle': 'Actual file structure observed',
  'obs.structFigure': ({ total, n }) => (
    <>Of {total} listings provided as files, the actual column structure has been observed for <strong>{n}</strong>.</>
  ),
  'obs.structNote': 'Listings not yet observed are queued for collection. This does not mean their data quality is low.',
  'obs.structUnavailable': 'This server version does not report the range of files whose structure was observed.',
  'obs.complTitle': 'Metadata filled in listings — by list type',
  'obs.complIntro':
    'File, API and standard-data listings have different sets of fields. Figures are therefore computed within each type only and are never summed or compared across types.',
  'obs.avgRate': 'average fill rate {p}%',
  'obs.noTarget': 'not computed for this type',
  'obs.complFail': 'Could not load the completeness distribution.',
  'obs.themeTitle': 'Distribution by theme — top {n} by listing count',
  'obs.themeFail': 'Could not load the theme distribution.',
  'obs.orgTitle': 'Distribution by publisher — top {n} by listing count',
  'obs.orgNote': 'Listing counts show how much an agency publishes, not a ranking of data quality.',
  'obs.orgFail': 'Could not load the publisher distribution.',
  'obs.familyTitle': 'Datasets that appear to belong to the same family',
  'obs.familyFail': 'Could not load family statistics.',
  'obs.familyUnavailable':
    'This server version has not yet computed family candidates. It does not mean there are zero candidates.',
  'obs.familyFigure': '{f} candidate groups ({m} listings) were found automatically.',
  'obs.familyNote': 'These are automatically found candidates, not confirmed families. ',
  'obs.familyStatus': '{label} {n}',
  'obs.changesTitle': 'Monthly changes',
  'obs.changesFail': 'Could not load change statistics.',
  'obs.changesAccumulating':
    'Added, modified and not-observed statistics become available once two or more monthly snapshots have accumulated. The first snapshot is currently being accumulated.',
  'obs.changesFigure': 'Changes observed between {base} and {cur}.',
  'obs.changesNote':
    "'Not observed in this snapshot' (MISSING_FROM_SNAPSHOT) does not mean the data was withdrawn. Only officially withdrawn items are shown as 'Officially withdrawn' (OFFICIALLY_WITHDRAWN).",

  // ---- About (AboutView)
  'about.heroTitle': 'Say what you want to do, and find Korean public data with the evidence',
  'about.heroBody': (
    <>
      Public Data Lens helps you find and compare the roughly 96,000 datasets registered on the
      Korean <a href="https://www.data.go.kr" target="_blank" rel="noreferrer">Public Data Portal</a> for
      a given purpose. It shows why a dataset matched and how much of it has actually been
      confirmed, so you can decide what to review first. Search and comparison results are
      produced by published rules: the same data and conditions give the same result, and the
      rule and version applied are always visible. The results do not vouch for the content or
      quality of the data itself. Data access and the original listings are on the Public Data Portal.
    </>
  ),
  'about.research': (
    <>
      Operated by the <a href="http://hike.cau.ac.kr" target="_blank" rel="noreferrer">HIKE Lab, Chung-Ang University</a>.
      It is an independent implementation developed ahead of the AI Ready Data standard
      (a Korean ICT association standard now being drafted), and also a project that tests the
      standard's feasibility against real public data.
    </>
  ),
  'about.catalogTitle': 'Catalog status',
  'about.statAll': 'Total listings',
  'about.statStruct': 'Actual file structure observed',
  'about.statSnapshot': 'Current snapshot (monthly)',
  'about.statAnalyzed': 'Analysis date',
  'about.loading': 'Loading status…',
  'about.principlesTitle': 'Data sources and operating principles',
  'about.principles': [
    <>Information is refreshed from the <a href="https://www.data.go.kr/data/15062804/fileData.do" target="_blank" rel="noreferrer">dataset listing</a> the Public Data Portal publishes every month. The actual data is not redistributed; data access and the original listings are on the Public Data Portal.</>,
    <>Descriptions registered in the listing and structure observed in actual files are kept apart. When a file could not be examined, that fact is shown too. On screen these are marked as catalog metadata (<code>CATALOG_METADATA_ONLY</code>) and actual file observation (<code>FILE_OBSERVATION</code>).</>,
    <>Usage logs do not store visitors' IP addresses. You can opt out of collection with your browser's DNT or GPC setting. <a href="/api/resources/privacy" target="_blank" rel="noreferrer">Privacy & logging notice</a></>,
    <>If you suspect an error in listing information, let us know via <a href="https://github.com/hike-lab/public-data-lens/issues" target="_blank" rel="noreferrer">GitHub Issues</a>. Confirmed findings are passed on to the publishing agency where appropriate.</>,
  ],

  // ---- Connect via MCP (ConnectView)
  'connect.heroTitle': 'Use the same data exploration from inside your AI assistant',
  'connect.heroBody': (
    <>
      Search, comparison and structure lookup are also available as an <strong>MCP (Model Context Protocol)</strong>
      server. Register the address below in any AI that supports MCP to explore data in
      conversation. It is free, needs no authentication, and applies the same rules as the web,
      so evidence and applied rule versions are shown alongside every result.
    </>
  ),
  'connect.copy': 'Copy',
  'connect.copied': 'Copied ✓',
  'connect.capTitle': 'What connecting gives you',
  'connect.capAsk': 'Ask in plain language',
  'connect.capQuote': '“Find EV charging station data that actually has latitude/longitude columns and would work for a regional comparison”',
  'connect.capSteps': 'The lens explores step by step',
  'connect.step1': 'Interpret the purpose',
  'connect.step2': 'Search by required columns',
  'connect.step3': 'Compare candidates',
  'connect.step4': 'Check actual structure',
  'connect.capOut': 'Results come with evidence',
  'connect.out1': 'Candidate datasets and expected roles — things to review first, not a final answer',
  'connect.out2': <>Evidence that coordinate columns were observed in the actual file (<code>FILE_OBSERVATION</code>)</>,
  'connect.out3': <>Limits and unverified items (<code>NOT_ASSESSED</code> · <code>CANDIDATE_ONLY</code>)</>,
  'connect.out4': 'Applied rule versions and the data snapshot',
  'connect.howTitle': 'How to connect, by AI service',
  'connect.claudeWeb': 'Claude web & desktop',
  'connect.claudeSteps': [
    <>On the web (claude.ai): <strong>Settings → Connectors → Add custom connector</strong></>,
    <>Paste the address above and add it</>,
    <>Ask directly in a conversation — for a structured plan, use <code>build_data_plan</code> from the prompt menu</>,
    <>To check the connection, ask: “Using this connector, tell me the current status of the public data catalog”</>,
  ],
  'connect.claudeCaveat': (
    <>
      On Team and Enterprise accounts the connector menu may not appear in member settings.
      An organisation admin has to add the connector first; members can then enable it under
      <strong> Settings → Connectors</strong> by pressing ‘Connect’. In the desktop app you can
      also register it in Claude Code as described below and then enable it under
      <strong> Settings → Connectors</strong>.
    </>
  ),
  'connect.claudePermission': (
    <>
      It is normal for Claude to ask permission for each tool call at first. Choose
      <strong> ‘Always allow’</strong> in the permission dialog to stop being asked. All tools on
      this server are read-only; they never add, modify or delete data.
    </>
  ),
  'connect.claudeCode': 'Claude Code (terminal)',
  'connect.claudeCodeCheck': <>Check: <code>claude mcp list</code> should show it as connected</>,
  'connect.chatgpt': 'ChatGPT web',
  'connect.chatgptStep1': <>Turn on <strong>Settings → Security & login → Developer mode</strong></>,
  'connect.chatgptStep2': <>Open <a href="https://chatgpt.com/plugins" target="_blank" rel="noreferrer">ChatGPT Plugins</a> → choose <code>+</code></>,
  'connect.chatgptStep3': 'Register the MCP app with:',
  'connect.chatgptTable': ({ mcpUrl }) => [
    ['Name', 'Public Data Lens'],
    ['Description', 'Search Korean public data by purpose, keyword or column, and check structure and evidence.'],
    ['Connection', 'Public endpoint'],
    ['MCP server URL', <code>{mcpUrl}</code>],
    ['Authentication', 'No Authentication'],
  ],
  'connect.chatgptStep4': 'After creating it, check the list of detected tools',
  'connect.chatgptStep5': <>New chat → <code>+</code> in the input box → Developer mode → select Public Data Lens</>,
  'connect.chatgptStep6': 'Ask directly in the conversation',
  'connect.chatgptCheck': (
    <>
      Check: "Using Public Data Lens, tell me the current status of the public data catalog."<br />
      Plan draft: "Using Public Data Lens, build a data plan for analysing EV charging stations."
    </>
  ),
  'connect.chatgptCaveat':
    'Developer mode is currently available on ChatGPT web for Plus, Pro, Business, Enterprise and Education accounts; organisation accounts may be restricted by admin policy.',
  'connect.other': 'Other MCP clients',
  'connect.otherBody': (
    <>
      Any client that supports remote MCP (streamable HTTP) can register the same address.
      Specification: <a href="/projects/public-data-lens/spec/tools/1.0" target="_blank" rel="noreferrer">tool schemas (JSON)</a>
    </>
  ),
  'connect.reconnect': (
    <>
      <strong>If newly added features do not appear,</strong> reconnect the connector once.
      AI apps remember the feature list from the moment of connection, so features added later
      show up only after reconnecting. Data updates are reflected immediately without reconnecting.
    </>
  ),
  'connect.askTitle': 'Things to ask',
  'connect.examplePrompts': [
    'I am reviewing a project to reuse closed schools — find public data I should look at',
    'Compare candidate datasets for analysing healthcare access for older adults',
    'Pick only tourism datasets that actually have latitude and longitude columns',
  ],
  'connect.featuresTitle': 'Available tools',
  'connect.featuresBody': (
    <>
      Dataset search · detail lookup · comparison of up to 5 · monthly changes · catalog statistics ·
      column-based search · actual file structure · <strong>data plan draft (build_data_plan)</strong> ·
      service guide — 9 tools in total. Describe what you want to do in one sentence and you get a
      plan draft with candidate datasets, their roles and selection basis, the fields expected to
      be used for joining, and the limits to check before use. Every result shows its evidence and
      the rule versions applied.
    </>
  ),

  // ---- Compare (CompareView)
  'compare.emptyHint': 'Select 2 to 5 datasets in search to see a structured comparison of facts.',
  'compare.oneSelected': '1 selected — select one more.',
  'compare.loading': 'Comparing…',
  'compare.thField': 'Field',
  'compare.remove': 'Remove',
  'compare.shared': ' (shared)',
  'compare.sharedHide': 'Hide shared fields',
  'compare.sharedShow': 'Show {n} shared fields',
  'compare.structTitle': 'Source column structure comparison',
  'compare.common': '{n} common columns:',
  'compare.none': 'none',
  'compare.onlyIn': 'Only in {title}:',
  'compare.totalCols': ' ({n} in total)',

  // ---- Change log (ChangesView)
  'changes.all': 'All',
  'changes.base': 'Compared: {b} → {c}',
  'changes.summary': 'Changes observed in this snapshot: ',
  'changes.count': '{label} {n}',
  'changes.empty': 'No changes with this status.',
  'changes.fields': 'Changed fields: {f}',
  'changes.more': 'More',

  // ---- Plan draft (PossibleUsesLens · PlanResult)
  'plan.status': ({ status }) => <>Plan status: draft (<code>{status}</code>)</>,
  'plan.quality': ({ q }) => <>Quality: not assessed (<code>{q}</code>)</>,
  'plan.interpretedTitle': 'Interpreted purpose',
  'plan.terms': 'Search terms {t}',
  'plan.region': ({ r, fromParam }) => ` · region ${r} (${fromParam ? 'given as parameter' : 'extracted from the sentence'})`,
  'plan.iterations': ' · {n} search iterations',
  'plan.needsTitle': 'Data needs',
  'plan.candidatesTitle': 'Candidate datasets (basis: listing and observed facts)',
  'plan.joinTitle': 'Possible join keys — all candidates (CANDIDATE_ONLY)',
  'plan.joinEmpty': 'No join key candidates with observation evidence — check the column definitions in the source directly.',
  'plan.missingTitle': 'Unsatisfied needs',
  'plan.nextTitle': 'Next checks',
  'plan.lensTitle': 'Data plan draft',
  'plan.lensIntro':
    'Write what you want to do in one sentence (Korean matches most reliably) and a deterministic rule (plan-assembly-v1.0) assembles candidates and limits — no LLM, no verdict, always a draft.',
  'plan.placeholder': ({ title }) => `e.g. ${title ? `${title.slice(0, 24)}로 ` : ''}지역 간 격차를 분석하고 싶다`,
  'plan.purposeAria': 'Purpose',
  'plan.submit': 'Assemble draft',
  'plan.assembling': 'Assembling…',
}
