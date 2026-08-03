import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import DatasetCardRow from './DatasetCardRow.jsx'

const EXAMPLES = [
  '어린이 보호구역',
  '산후조리원 현황',
  '무더위 쉼터',
  '식품 제조 공장',
  '버스 정류장 위치',
  '관광지 방문객',
]

// 컬럼 모드 예시 — 실파일에서 자주 관측되는 원본 컬럼명 조합
const COLUMN_EXAMPLES = ['위도, 경도', '주소, 전화번호', '사업자등록번호', '설치연도']

const REGIONS = [
  ['', '지역 전체'], ['KR-11', '서울'], ['KR-26', '부산'], ['KR-27', '대구'],
  ['KR-28', '인천'], ['KR-29', '광주'], ['KR-30', '대전'], ['KR-31', '울산'],
  ['KR-50', '세종'], ['KR-41', '경기'], ['KR-42', '강원'], ['KR-43', '충북'],
  ['KR-44', '충남'], ['KR-45', '전북'], ['KR-46', '전남'], ['KR-47', '경북'],
  ['KR-48', '경남'], ['KR-49', '제주'],
]

const CYCLES = [
  ['', '주기 전체'], ['DAILY', '일간'], ['WEEKLY', '주간'], ['MONTHLY', '월간'],
  ['QUARTERLY', '분기'], ['SEMIANNUAL', '반기'], ['ANNUAL', '연간'], ['IRREGULAR', '수시'],
]

const FORMATS = ['', 'CSV', 'JSON', 'XML', 'XLSX', 'PDF', 'SHP']

/* ---- 결정론적 질의 해석 — LLM 없이 검색어에서 조건을 읽어낸다.
   "서울 무더위 쉼터 CSV" → 지역·포맷을 필터로 옮기고 키워드만 검색.
   MCP 호스트 LLM이 하는 필터 매핑과 같은 의미론을 웹에서 재현하는 기준점. ---- */
const REGION_ALIAS = (() => {
  const m = {}
  REGIONS.slice(1).forEach(([code, name]) => { m[name] = code })
  Object.assign(m, {
    서울시: 'KR-11', 서울특별시: 'KR-11', 부산시: 'KR-26', 부산광역시: 'KR-26',
    대구시: 'KR-27', 대구광역시: 'KR-27', 인천시: 'KR-28', 인천광역시: 'KR-28',
    광주시: 'KR-29', 광주광역시: 'KR-29', 대전시: 'KR-30', 대전광역시: 'KR-30',
    울산시: 'KR-31', 울산광역시: 'KR-31', 세종시: 'KR-50', 세종특별자치시: 'KR-50',
    경기도: 'KR-41', 강원도: 'KR-42', 강원특별자치도: 'KR-42',
    충청북도: 'KR-43', 충청남도: 'KR-44', 전라북도: 'KR-45', 전북특별자치도: 'KR-45',
    전라남도: 'KR-46', 경상북도: 'KR-47', 경상남도: 'KR-48',
    제주도: 'KR-49', 제주특별자치도: 'KR-49',
  })
  return m
})()
const FORMAT_ALIAS = { CSV: 'CSV', JSON: 'JSON', XML: 'XML', XLSX: 'XLSX', 엑셀: 'XLSX', EXCEL: 'XLSX', PDF: 'PDF', SHP: 'SHP' }
const CYCLE_ALIAS = {
  일간: 'DAILY', 매일: 'DAILY', 주간: 'WEEKLY', 매주: 'WEEKLY', 월간: 'MONTHLY', 매월: 'MONTHLY',
  분기: 'QUARTERLY', 반기: 'SEMIANNUAL', 연간: 'ANNUAL', 매년: 'ANNUAL', 수시: 'IRREGULAR',
}
const TYPE_ALIAS = { API: 'API', 파일: 'FILE', FILE: 'FILE', 표준: 'STD', STD: 'STD' }
const CYCLE_LABEL = Object.fromEntries(CYCLES.map(([v, l]) => [v, l]))

function interpretQuery(raw) {
  const tokens = raw.split(/\s+/).filter(Boolean)
  const found = {}
  const labels = []
  const rest = []
  for (const t of tokens) {
    const up = t.toUpperCase()
    if (!found.region && REGION_ALIAS[t]) {
      found.region = REGION_ALIAS[t]
      labels.push(`지역 ${t.replace(/(특별자치|특별|광역)?(시|도)$/, '')}`)
    } else if (!found.format && (FORMAT_ALIAS[t] || FORMAT_ALIAS[up])) {
      found.format = FORMAT_ALIAS[t] || FORMAT_ALIAS[up]
      labels.push(`포맷 ${found.format}`)
    } else if (!found.updateCycle && CYCLE_ALIAS[t]) {
      found.updateCycle = CYCLE_ALIAS[t]
      labels.push(`주기 ${CYCLE_LABEL[CYCLE_ALIAS[t]]}`)
    } else if (!found.listType && TYPE_ALIAS[up]) {
      found.listType = TYPE_ALIAS[up]
      labels.push(`유형 ${TYPE_ALIAS[up]}`)
    } else {
      rest.push(t)
    }
  }
  return { found, labels, rest: rest.join(' ') }
}

export default function SearchView({ onOpen, compareIds, onToggleCompare, seed }) {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({
    listType: '', region: '', includeInferred: true, updateCycle: '', format: '',
  })
  const [result, setResult] = useState(null)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const runSearch = useCallback(
    async (cursor = null, q = query, f = filters) => {
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
        })
        setResult(body)
        setItems((prev) => (cursor ? [...prev, ...body.data.items] : body.data.items))
      } catch (e) {
        setError(`${e.code || ''} ${e.message}`)
      } finally {
        setLoading(false)
      }
    },
    [query, filters],
  )

  useEffect(() => {
    runSearch() // 초기: 최신 수정순 목록
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 컨시어지 보완 노드에서 넘어온 프리필 질의
  useEffect(() => {
    if (!seed?.q) return
    setQuery(seed.q)
    setPristine(false)
    runSearch(null, seed.q, filters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seed?.t])

  // 검색어에서 읽어낸 조건 표시(해석 배너) — keys는 자동 적용된 필터 키(해제용)
  const [interp, setInterp] = useState(null)
  // 첫 화면에만 예시를 보여준다 — 검색을 시작하면 화면을 비운다
  const [pristine, setPristine] = useState(true)
  // 필터는 기본 접힘 — 활성 조건은 칩으로 요약 노출
  const [showFilters, setShowFilters] = useState(false)

  const submit = (e) => {
    e.preventDefault()
    setPristine(false)
    const { found, labels, rest } = interpretQuery(query)
    const keys = Object.keys(found)
    if (keys.length && rest !== query.trim()) {
      const next = { ...filters, ...found }
      setFilters(next)
      setQuery(rest)
      setInterp({ labels, keys, raw: query })
      runSearch(null, rest, next)
    } else {
      setInterp(null)
      runSearch()
    }
  }

  const dismissInterp = () => {
    if (!interp) return
    const next = { ...filters }
    interp.keys.forEach((k) => { next[k] = '' })
    setFilters(next)
    setQuery(interp.raw)
    setInterp(null)
    runSearch(null, interp.raw, next)
  }

  // 컬럼 기준 검색(v1.3) — 원본 컬럼명 부분 일치(AND), 구조 확인분 내에서만
  const [mode, setMode] = useState('keyword') // 'keyword' | 'columns'
  const [colQuery, setColQuery] = useState('')
  const runColumnSearch = async (e, q = colQuery) => {
    e?.preventDefault()
    setPristine(false)
    const kws = q.split(',').map((k) => k.trim()).filter(Boolean)
    if (!kws.length) return
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
    setInterp(null) // 수동 필터 조작 시 해석 배너는 더 이상 유효하지 않다
    runSearch(null, query, next)
  }

  return (
    <section className={pristine ? 'search-home' : undefined}>
      {pristine && (
        <div className="hero">
          <h2 className="hero-title">
            공공데이터 {result ? result.data.totalEstimate.toLocaleString() : '96,056'}건을<br />
            근거와 함께 찾아드립니다
          </h2>
          <p className="hero-sub">
            목록 검색부터 실파일에서 확인한 컬럼 구조까지 — 웹과 AI(MCP)가 같은 판정 엔진을 씁니다
          </p>
        </div>
      )}
      <form
        className="searchbar unified"
        onSubmit={mode === 'keyword' ? submit : runColumnSearch}
      >
        <div className="search-shell">
          <div className="seg" role="tablist" aria-label="검색 방식">
            <button
              type="button"
              className={mode === 'keyword' ? 'on' : ''}
              onClick={() => setMode('keyword')}
            >
              키워드
            </button>
            <button
              type="button"
              className={mode === 'columns' ? 'on' : ''}
              onClick={() => setMode('columns')}
              title="실제 파일에서 관측된 원본 컬럼명으로 데이터셋을 찾습니다"
            >
              컬럼
            </button>
          </div>
          {mode === 'keyword' ? (
            <input
              key="kw"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="무엇을 찾으시나요? — 지역·포맷을 함께 적어도 됩니다"
              maxLength={500}
            />
          ) : (
            <input
              key="col"
              value={colQuery}
              onChange={(e) => setColQuery(e.target.value)}
              placeholder="원본 컬럼명 — 쉼표로 여러 개 (예: 위도, 경도)"
              maxLength={200}
            />
          )}
        </div>
        <button type="submit" disabled={loading}>검색</button>
      </form>
      {mode === 'columns' && (
        <p className="search-hint">
          실제 파일에서 관측된 원본 컬럼명과 부분 일치하는 데이터셋을 찾습니다 — 여러 개를
          쉼표로 적으면 모두 가진 것만(AND) 반환합니다.
        </p>
      )}
      {mode === 'keyword' && interp && (
        <p className="interp">
          <span className="interp-mark">해석</span>
          검색어에서 <strong>{interp.labels.join(' · ')}</strong> 조건을 읽어 적용했습니다
          <button type="button" className="link" onClick={dismissInterp}>원문 그대로 검색</button>
        </p>
      )}

      {pristine && (
        <div className="examples">
          <span className="examples-label">예시</span>
          {(mode === 'keyword' ? EXAMPLES : COLUMN_EXAMPLES).map((ex) => (
            <button
              key={ex}
              className="chip"
              onClick={() => {
                setPristine(false)
                if (mode === 'keyword') { setQuery(ex); runSearch(null, ex, filters) }
                else { setColQuery(ex); runColumnSearch(null, ex) }
              }}
            >
              {ex}
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
          전체 목록 둘러보기 →
        </button>
      )}

      {!pristine && result && (
        <div className="toolbar">
          <p
            className="result-meta"
            title={result.data.ranking
              ? `랭킹 ${result.data.ranking.method} (${result.data.ranking.version})`
              : undefined}
          >
            총 {result.data.totalEstimate.toLocaleString()}건
            {result.data.coverage
              ? <> · 구조가 관측된 {result.data.coverage.searchedRecords.toLocaleString()}건 중 검색</>
              : result.data.ranking?.method?.includes('bm25')
                ? ' · 관련도순'
                : ' · 최신 수정순'}
          </p>
          {mode === 'keyword' && (
            <div className="toolbar-right">
              {['listType', 'region', 'updateCycle', 'format'].filter((k) => filters[k]).map((k) => (
                <button key={k} className="fchip" onClick={() => setFilter(k, '')} title="조건 해제">
                  {k === 'region'
                    ? REGIONS.find(([c]) => c === filters[k])?.[1]
                    : k === 'updateCycle' ? CYCLE_LABEL[filters[k]] : filters[k]}
                  <span aria-hidden> ×</span>
                </button>
              ))}
              <button
                type="button"
                className={`filter-toggle${showFilters ? ' open' : ''}`}
                onClick={() => setShowFilters((v) => !v)}
              >
                필터
              </button>
            </div>
          )}
        </div>
      )}

      {showFilters && mode === 'keyword' && (
      <div className="filters">
        <select value={filters.listType} onChange={(e) => setFilter('listType', e.target.value)}>
          <option value="">유형 전체</option>
          <option value="FILE">FILE</option>
          <option value="API">API</option>
          <option value="STD">표준(STD)</option>
        </select>
        <select value={filters.region} onChange={(e) => setFilter('region', e.target.value)}>
          {REGIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <label className="inferred">
          <input
            type="checkbox"
            checked={filters.includeInferred}
            onChange={(e) => setFilter('includeInferred', e.target.checked)}
          />
          추론 지역 포함
        </label>
        <select value={filters.updateCycle} onChange={(e) => setFilter('updateCycle', e.target.value)}>
          {CYCLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select value={filters.format} onChange={(e) => setFilter('format', e.target.value)}>
          {FORMATS.map((f) => <option key={f} value={f}>{f || '포맷 전체'}</option>)}
        </select>
      </div>
      )}

      {error && <p className="error">{error}</p>}
      {!pristine && result?.warnings
        .filter((w) => !w.startsWith('본 결과는'))
        .map((w, i) => (
          // 계약 경고 원문은 툴팁으로 보존하고, 화면에는 소비자 언어로 순화해 보여준다
          <p className="notice" key={i} title={w}>
            {w.includes('INFERRED_')
              ? '지역 조건에는 추론된 지역도 포함됩니다 — 각 결과의 지역 배지(명시/추론)에서 근거를 확인할 수 있습니다.'
              : w}
          </p>
        ))}

      {!pristine && result && !loading && items.length === 0 && (
        <div className="empty-state">
          <p className="empty-title">조건에 맞는 데이터를 찾지 못했습니다</p>
          <p className="empty-body">
            키워드를 줄이거나 필터를 해제해 보세요. 찾는 방식이 막막하면 우측 상단
            <strong> AI에 연결</strong>로 대화하며 탐색할 수도 있습니다.
          </p>
        </div>
      )}

      {!pristine && (<>
      <ul className="results">
        {items.map((item) => (
          <DatasetCardRow
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
          {loading ? '불러오는 중…' : '결과 더 보기'}
        </button>
      )}
      </>)}
    </section>
  )
}
