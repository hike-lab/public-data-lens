import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import DatasetRow from './DatasetRow.jsx'
import WarningPanel from './WarningPanel.jsx'
import { CoveragePopulation } from './CoverageIndicator.jsx'
import { PlanResult } from './PossibleUsesLens.jsx'

// 예시 질의(키워드·컬럼·목적)는 strings.*.jsx의 search.*Examples — 질의(q)는 한국어 카탈로그
// 기준으로 두 언어에서 같고, 칩에 보이는 문안(label)만 언어를 따른다.
// 지역·주기 라벨은 labels.js(REGION_LABEL·UPDATE_CYCLE_LABEL)에서 온다.

const FORMATS = ['', 'CSV', 'JSON', 'XML', 'XLSX', 'PDF', 'SHP']

// 검색 상태(질의·필터·모드)를 URL 쿼리로 직렬화 — 공유·북마크·복원의 단일 형식
function toUrlParams(q, f, m, cq) {
  const p = new URLSearchParams()
  if (m === 'columns') {
    p.set('mode', 'columns')
    if (cq) p.set('cols', cq)
    return p.toString()
  }
  if (m === 'purpose') {
    p.set('mode', 'purpose')
    if (cq) p.set('purpose', cq)
    return p.toString()
  }
  if (q) p.set('q', q)
  for (const k of ['listType', 'region', 'updateCycle', 'format']) if (f[k]) p.set(k, f[k])
  if (!f.includeInferred) p.set('inferred', '0')
  return p.toString()
}

export default function SearchView({
  onOpen, compareIds, onToggleCompare, seed, status, urlParams, onUrlChange, planAvailable,
}) {
  const { t, L } = useLang()
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({
    listType: '', region: '', includeInferred: true, updateCycle: '', format: '',
  })
  const [result, setResult] = useState(null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 사용자가 해석을 해제하면(원문 그대로 검색) 다음 제출 전까지 interpret를 끈다
  const [interpretOff, setInterpretOff] = useState(false)
  // 정렬 선택(v1.6) — ''=기본(질의 시 관련도), 'modified'=최신 수정순
  const [sortMode, setSortMode] = useState('')

  /* 질의 해석은 서버(query-interpret-v1.0)가 한다 — 프론트 별칭 사전·해석 로직 제거(STEP 8).
     서버가 반환한 interpretedFilters[]를 배너로 표시하고, 해제 시 interpret=false로 재검색. */
  const interpretedLabel = (f) => {
    const v = f.field === 'region'
      ? (L.REGION_LABEL[f.value] || f.value)
      : f.field === 'updateCycle' ? (L.UPDATE_CYCLE_LABEL[f.value] || f.value) : f.value
    return `${L.INTERPRETED_FIELD_LABEL[f.field] || f.field} ${v}`
  }

  const runSearch = useCallback(
    async (cursor = null, q = query, f = filters, interpret = !interpretOff, sortArg = sortMode) => {
      setLoading(true)
      setError(null)
      try {
        const body = await api.search({
          query: q || undefined,
          listType: f.listType || undefined,
          region: f.region || undefined,
          includeInferred: f.includeInferred,
          updateCycle: f.updateCycle || undefined,
          format: f.format || undefined,
          cursor: cursor || undefined,
          pageSize: 20,
          // 질의 해석은 서버 규칙(query-interpret-v1.0) — 근거가 interpretedFilters로 돌아온다
          interpret: interpret && q ? true : undefined,
          sort: sortArg || undefined,
        })
        setResult(body)
        setItems((prev) => (cursor ? [...prev, ...body.data.items] : body.data.items))
      } catch (e) {
        setError(`${e.code || ''} ${e.message}`)
      } finally {
        setLoading(false)
      }
    },
    [query, filters, interpretOff, sortMode],
  )

  // URL 반영 — 검색을 실행한 조건을 주소창에 남긴다(replace — 히스토리를 더럽히지 않음)
  const syncUrl = (q, f, m = 'keyword', cq = '') => {
    onUrlChange?.(toUrlParams(q, f, m, cq))
  }

  // 컨시어지 보완 노드에서 넘어온 프리필 질의
  useEffect(() => {
    if (!seed?.q) return
    setQuery(seed.q)
    setPristine(false)
    runSearch(null, seed.q, filters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seed?.t])

  // 첫 화면에만 예시를 보여준다 — 검색을 시작하면 화면을 비운다
  const [pristine, setPristine] = useState(true)
  // 필터는 기본 접힘 — 활성 조건은 칩으로 요약 노출
  const [showFilters, setShowFilters] = useState(false)

  const submit = (e) => {
    e.preventDefault()
    setPristine(false)
    setInterpretOff(false) // 새 제출은 해석 재개
    runSearch(null, query, filters, true)
    syncUrl(query, filters)
  }

  // '원문 그대로 검색' — 서버 해석을 끄고 같은 질의를 재실행
  const dismissInterp = () => {
    setInterpretOff(true)
    runSearch(null, query, filters, false)
  }

  // 컬럼 기준 검색(v1.3) — 원본 컬럼명 부분 일치(AND), 구조 확인분 내에서만
  const [mode, setMode] = useState('keyword') // 'keyword' | 'columns' | 'purpose'
  const [colQuery, setColQuery] = useState('')

  // 목적 기준 탐색(v1.5) — 이름 대신 하려는 일로. POST /api/plan(결정론 조립기, 항상 초안)
  const [purposeQuery, setPurposeQuery] = useState('')
  const [planBody, setPlanBody] = useState(null)
  const runPurposeSearch = async (e, p = purposeQuery) => {
    e?.preventDefault()
    if (p.trim().length < 2) return
    setPristine(false)
    setPlanBody(null)
    syncUrl('', filters, 'purpose', p)
    setLoading(true)
    setError(null)
    try {
      setPlanBody(await api.plan(p))
    } catch (err) {
      setError(`${err.code || ''} ${err.message}`)
    } finally {
      setLoading(false)
    }
  }
  const runColumnSearch = async (e, q = colQuery) => {
    e?.preventDefault()
    setPristine(false)
    const kws = q.split(',').map((k) => k.trim()).filter(Boolean)
    if (!kws.length) return
    syncUrl('', filters, 'columns', q)
    setLoading(true)
    setError(null)
    try {
      const body = await api.searchColumns(kws)
      setResult(body)
      setItems(body.data.items)
    } catch (err) {
      setError(`${err.code || ''} ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const setFilter = (k, v) => {
    const next = { ...filters, [k]: v }
    setFilters(next)
    runSearch(null, query, next)
    syncUrl(query, next)
  }

  // 최초 마운트: URL에 담긴 검색 상태를 복원한다(공유·북마크·뒤로가기)
  useEffect(() => {
    const p = urlParams
    if (p && p.get('mode') === 'columns' && p.get('cols')) {
      setMode('columns')
      setColQuery(p.get('cols'))
      runColumnSearch(null, p.get('cols'))
      return
    }
    if (p && p.get('mode') === 'purpose' && p.get('purpose')) {
      setMode('purpose')
      setPurposeQuery(p.get('purpose'))
      runPurposeSearch(null, p.get('purpose'))
      return
    }
    const restored = { ...filters }
    let any = false
    for (const k of ['listType', 'region', 'updateCycle', 'format']) {
      if (p?.get(k)) { restored[k] = p.get(k); any = true }
    }
    if (p?.get('inferred') === '0') { restored.includeInferred = false; any = true }
    const q = p?.get('q') || ''
    if (q || any) {
      setQuery(q)
      setFilters(restored)
      setPristine(false)
      runSearch(null, q, restored)
    } else {
      runSearch() // 초기: 최신 수정순 목록(pristine 홈의 Live 블록 데이터)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const examples = mode === 'keyword'
    ? t('search.examples')
    : mode === 'columns' ? t('search.columnExamples') : t('search.purposeExamples')
  const cycles = [['', t('search.cycleAll')], ...Object.entries(L.UPDATE_CYCLE_LABEL)]

  return (
    <section className={pristine ? 'search-home' : undefined}>
      {pristine && (
        <div className="hero">
          {/* 제목=행동 유도 질문, 부제=철학 선언(숫자 없음 — 건수는 소개·푸터가 담당) */}
          <h2 className="hero-title">{t('search.heroTitle')}</h2>
          <p className="hero-sub">{t('search.heroSub')}</p>
        </div>
      )}
      <form
        className="searchbar unified"
        onSubmit={mode === 'keyword' ? submit : mode === 'columns' ? runColumnSearch : runPurposeSearch}
      >
        <div className="search-shell">
          <div className="seg" role="tablist" aria-label={t('search.modeAria')}>
            <button
              type="button"
              className={mode === 'keyword' ? 'on' : ''}
              onClick={() => setMode('keyword')}
            >
              {t('search.modeKeyword')}
            </button>
            <button
              type="button"
              className={mode === 'columns' ? 'on' : ''}
              onClick={() => setMode('columns')}
              title={t('search.modeColumnsTitle')}
            >
              {t('search.modeColumns')}
            </button>
            {planAvailable && (
              <button
                type="button"
                className={mode === 'purpose' ? 'on' : ''}
                onClick={() => setMode('purpose')}
                title={t('search.modePurposeTitle')}
              >
                {t('search.modePurpose')}
              </button>
            )}
          </div>
          {mode === 'keyword' && (
            <input
              key="kw"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('search.phKeyword')}
              maxLength={500}
            />
          )}
          {mode === 'columns' && (
            <input
              key="col"
              value={colQuery}
              onChange={(e) => setColQuery(e.target.value)}
              placeholder={t('search.phColumns')}
              maxLength={200}
            />
          )}
          {mode === 'purpose' && (
            <input
              key="pp"
              value={purposeQuery}
              onChange={(e) => setPurposeQuery(e.target.value)}
              placeholder={t('search.phPurpose')}
              maxLength={200}
            />
          )}
        </div>
        <button type="submit" disabled={loading}>{mode === 'purpose' ? t('search.submitPlan') : t('search.submit')}</button>
      </form>
      {mode === 'columns' && <p className="search-hint">{t('search.hintColumns')}</p>}
      {mode === 'purpose' && <p className="search-hint">{t('search.hintPurpose')}</p>}
      {/* 영어 표면: 카탈로그가 한국어라는 안내(한국어 표면에서는 빈 문자열 → 생략) */}
      {pristine && t('search.hintLang') && <p className="search-hint">{t('search.hintLang')}</p>}
      {mode === 'keyword' && result?.data?.interpretedFilters?.length > 0 && (
        <p className="interp">
          <span className="interp-mark">{t('search.interpMark')}</span>
          {t('search.interpApplied', { filters: result.data.interpretedFilters.map(interpretedLabel).join(' · ') })}
          <small> ({result.data.interpretedFilters[0].ruleId})</small>
          <button type="button" className="link" onClick={dismissInterp}>{t('search.interpDismiss')}</button>
        </p>
      )}

      {pristine && (
        <div className="examples">
          <span className="examples-label">{t('search.examplesLabel')}</span>
          {examples.map((ex) => (
            <button
              key={ex.q}
              className="chip"
              lang="ko"
              onClick={() => {
                setPristine(false)
                if (mode === 'keyword') { setQuery(ex.q); runSearch(null, ex.q, filters); syncUrl(ex.q, filters) }
                else if (mode === 'columns') { setColQuery(ex.q); runColumnSearch(null, ex.q) }
                else { setPurposeQuery(ex.q); runPurposeSearch(null, ex.q) }
              }}
            >
              {ex.label}
            </button>
          ))}
        </div>
      )}

      {pristine && (
        <button
          type="button"
          className="browse-all"
          onClick={() => { setPristine(false); runSearch() }}
        >
          {t('search.browseAll')}
        </button>
      )}

      {/* 홈은 검색 단독(2026-08-04 결정) — 쇼케이스 블록은 '둘러보기',
          커버리지·판정 인프라는 '소개' 하단으로 이동 */}

      {!pristine && mode !== 'purpose' && result && (
        <div className="toolbar">
          <p
            className="result-meta"
            title={result.data.ranking
              ? t('search.rankingTitle', { method: result.data.ranking.method, version: result.data.ranking.version })
              : undefined}
          >
            {/* 정렬·검색 기준은 계약 필드(ranking.basis, v1.5)에서 — 문자열 추론 금지 */}
            {t('search.total', { n: result.data.totalEstimate.toLocaleString() })}
            {result.data.ranking?.basis === 'relevance' && t('search.byRelevance')}
            {result.data.ranking?.basis === 'modified_date' && t('search.byModified')}
            {result.data.coverage && (
              <> · <CoveragePopulation
                searched={result.data.coverage.searchedRecords}
                total={result.data.coverage.fileRecordsTotal}
              /></>
            )}
            {result.data.coverage && items.length < result.data.totalEstimate && (
              t('search.topShown', { n: items.length })
            )}
          </p>
          {mode === 'keyword' && (
            <div className="toolbar-right">
              {query && (
                <select
                  className="sort-select"
                  aria-label={t('search.sortAria')}
                  value={sortMode}
                  onChange={(e) => {
                    const v = e.target.value
                    setSortMode(v)
                    runSearch(null, query, filters, !interpretOff, v)
                  }}
                >
                  <option value="">{t('search.sortRelevance')}</option>
                  <option value="modified">{t('search.sortModified')}</option>
                </select>
              )}
              {['listType', 'region', 'updateCycle', 'format'].filter((k) => filters[k]).map((k) => (
                <button key={k} className="fchip" onClick={() => setFilter(k, '')} title={t('search.chipRemove')}>
                  {k === 'region'
                    ? L.REGION_LABEL[filters[k]] || filters[k]
                    : k === 'updateCycle' ? L.UPDATE_CYCLE_LABEL[filters[k]] : filters[k]}
                  <span aria-hidden> ×</span>
                </button>
              ))}
              <button
                type="button"
                className={`filter-toggle${showFilters ? ' open' : ''}`}
                onClick={() => setShowFilters((v) => !v)}
              >
                {t('search.filters')}
              </button>
            </div>
          )}
        </div>
      )}

      {showFilters && mode === 'keyword' && (
      <div className="filters">
        <select value={filters.listType} onChange={(e) => setFilter('listType', e.target.value)}>
          <option value="">{t('search.typeAll')}</option>
          <option value="FILE">FILE</option>
          <option value="API">API</option>
          <option value="STD">{t('search.typeStd')}</option>
        </select>
        <select value={filters.region} onChange={(e) => setFilter('region', e.target.value)}>
          {Object.entries(L.REGION_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <label className="inferred">
          <input
            type="checkbox"
            checked={filters.includeInferred}
            onChange={(e) => setFilter('includeInferred', e.target.checked)}
          />
          {t('search.includeInferred')}
        </label>
        <select value={filters.updateCycle} onChange={(e) => setFilter('updateCycle', e.target.value)}>
          {cycles.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select value={filters.format} onChange={(e) => setFilter('format', e.target.value)}>
          {FORMATS.map((f) => <option key={f} value={f}>{f || t('search.formatAll')}</option>)}
        </select>
      </div>
      )}

      {error && <p className="error">{error}</p>}
      {loading && mode === 'purpose' && <p className="loading">{t('search.assembling')}</p>}
      {!pristine && mode !== 'purpose' && (
        <WarningPanel warnings={result?.warnings} notices={result?.notices} />
      )}

      {/* 목적 모드 결과 — 상세의 '활용 초안' 렌즈와 같은 단일 렌더러(PlanResult) */}
      {!pristine && mode === 'purpose' && planBody && (
        <div className="profile plan-standalone">
          <PlanResult body={planBody} onOpen={onOpen} />
        </div>
      )}

      {/* 빈 결과(§4.5) — 조회 범위를 함께 말해 '데이터 부재'로 읽히지 않게 한다 */}
      {!pristine && mode !== 'purpose' && result && !loading && items.length === 0 && (
        <div className="empty-state">
          <p className="empty-title">{t('search.emptyTitle')}</p>
          <p className="empty-body">
            {t('search.emptyScope', { snapshot: result.meta?.sourceSnapshot })}
            {result.data.coverage
              ? t('search.emptyColumns', { n: result.data.coverage.searchedRecords.toLocaleString() })
              : t('search.emptyAll')}
            <br />
            {t('search.emptyAdvice')}
          </p>
        </div>
      )}

      {!pristine && mode !== 'purpose' && (<>
      <ul className="results">
        {items.map((item) => (
          <DatasetRow
            key={item.recordId}
            item={item}
            onOpen={onOpen}
            compared={compareIds.includes(item.recordId)}
            compareFull={compareIds.length >= 5}
            onToggleCompare={onToggleCompare}
          />
        ))}
      </ul>

      {result?.data.nextCursor && result?.data.hasMore && (
        <button
          className="more"
          disabled={loading}
          onClick={() => runSearch(result.data.nextCursor)}
        >
          {loading ? t('common.loading') : t('search.more')}
        </button>
      )}
      </>)}
    </section>
  )
}
