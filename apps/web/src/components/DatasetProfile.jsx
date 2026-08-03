import { useEffect, useState } from 'react'
import { api } from '../api.js'

const VIEWS = [
  ['card', '카드'],
  ['structure', '데이터 구조'],
  ['normalized', '정규화'],
  ['source', '원본'],
  ['jsonld', 'JSON-LD'],
]

const COVERAGE_LABEL = {
  AVAILABLE: '구조 확인됨',
  PARTIAL: '일부 파일만 확인됨',
  NOT_COLLECTED: '아직 관측되지 않음',
  COLLECTION_FAILED: '관측 실패',
  API_STRUCTURE_NOT_SUPPORTED_YET: 'API 구조는 차기 지원',
}

const EXAMPLE_STATUS_LABEL = {
  NO_NON_NULL_VALUES: '값 없음',
  WITHHELD_BY_LICENSE: '라이선스 보류',
  WITHHELD_BY_SAFETY: '안전 비공개',
  NOT_COLLECTED: '미수집',
  COLLECTION_FAILED: '수집 실패',
}

// 완전성 점검 필드의 한글 표기 — 점수(기재 n/16)의 분해 근거 체크리스트용
const FIELD_LABEL = {
  title: '제목', theme: '분류', org_name: '제공기관', update_cycle: '갱신주기',
  keywords: '키워드', description: '설명', license: '이용허락', created_date: '등록일',
  modified_date: '수정일', list_url: '원문 URL', spatial: '공간범위', temporal: '시간범위',
  data_limits: '이용제한', format: '포맷', row_count: '행 수', file_data_name: '파일명',
  api_type: 'API 유형', traffic: '트래픽',
}

const FRESH_LABEL = {
  FRESH: { text: '최신', cls: 'fresh' },
  POSSIBLY_STALE: { text: '갱신 지연 가능', cls: 'stale' },
  UNKNOWN: { text: '최신성 판단 불가', cls: 'unknown' },
}

export default function DatasetProfile({ recordId, onClose }) {
  const [view, setView] = useState('card')
  const [body, setBody] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setBody(null)
    setError(null)
    const load = view === 'structure' ? api.structure(recordId) : api.dataset(recordId, view)
    load.then(setBody).catch((e) => setError(e.message))
  }, [recordId, view])

  const ds = view === 'structure' ? null : body?.data?.dataset
  const st = view === 'structure' ? body?.data : null

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div className="drawer-tabs">
            {VIEWS.map(([v, label]) => (
              <button key={v} className={view === v ? 'tab active' : 'tab'} onClick={() => setView(v)}>
                {label}
              </button>
            ))}
          </div>
          <button className="close" onClick={onClose}>✕</button>
        </div>

        {error && <p className="error">{error}</p>}
        {!body && !error && <p className="loading">불러오는 중…</p>}

        {body?.warnings
          ?.filter((w) => !w.startsWith('본 결과는'))
          .map((w, i) => <p className="warning" key={i}>⚠ {w}</p>)}

        {ds && view === 'card' && <CardView ds={ds} />}
        {st && <StructureView st={st} />}
        {ds && view !== 'card' && (
          <pre className="json-view">{JSON.stringify(ds, null, 2)}</pre>
        )}

        {body && (
          <p className="drawer-meta">
            스냅샷 {body.meta.sourceSnapshot} · 규칙 {body.meta.ruleVersions.join(', ') || '—'}
          </p>
        )}
      </aside>
    </div>
  )
}

function CardView({ ds }) {
  const fresh = FRESH_LABEL[ds.freshness?.status] || FRESH_LABEL.UNKNOWN
  return (
    <div className="profile">
      <h2>
        <span className={`type type-${ds.listType}`}>{ds.listType}</span> {ds.title}
      </h2>
      <p className="org">{ds.orgName}</p>

      <div className="prop-grid">
        <Prop k="분류" v={ds.theme?.top ? `${ds.theme.top}${ds.theme.sub ? ' › ' + ds.theme.sub : ''}` : '—'} />
        <Prop k="포맷" v={ds.formats?.join(', ') || '—'} />
        <Prop k="업데이트 주기" v={ds.updateCycleRaw || '—'} />
        <Prop k="이용허락" v={ds.license?.raw || '—'} />
        <Prop k="등록일" v={ds.createdDate || '—'} />
        <Prop k="수정일" v={ds.modifiedDate || '—'} />
        <Prop k="공간범위" v={ds.spatial || '미기재'} />
        <Prop k="시간범위" v={ds.temporal || '미기재'} />
        {ds.rowCount != null && <Prop k="전체 행" v={ds.rowCount.toLocaleString()} />}
        {ds.apiType && <Prop k="API 유형" v={ds.apiType} />}
      </div>

      <div className="judgments">
        <span
          className="completeness large"
          title={`${ds.completeness.profile} 프로파일 · ${ds.completeness.rule}`}
        >
          목록 기재 {ds.completeness.filledFields}/{ds.completeness.totalFields}
          <small>
            {' '}({ds.completeness.profile} 프로파일 ·{' '}
            {ds.completeness.typical
              ? `동일 유형의 ${ds.completeness.typicalShare}%와 같은 표준 수준`
              : `유형 내 상위 ${ds.completeness.topPercent}%`})
          </small>
        </span>
        <span className={`freshness ${fresh.cls}`} title={ds.freshness?.note || ''}>
          {fresh.text}
          {ds.freshness?.ageDays != null && <small> · 수정 후 {ds.freshness.ageDays}일</small>}
        </span>
      </div>

      {ds.completeness.fields && (
        <div className="field-checklist">
          {Object.entries(ds.completeness.fields).map(([f, filled]) => (
            <span key={f} className={filled ? 'fc filled' : 'fc missing'}>
              {filled ? '✓' : '—'} {FIELD_LABEL[f] || f}
            </span>
          ))}
        </div>
      )}

      {ds.description && (
        <>
          <h3>설명</h3>
          <p className="desc">{ds.description}</p>
        </>
      )}
      {ds.dataLimits && (
        <>
          <h3>데이터 한계 (기관 기재)</h3>
          <p className="desc">{ds.dataLimits}</p>
        </>
      )}
      {ds.keywords?.length > 0 && (
        <div className="keywords">
          {ds.keywords.map((k) => <span key={k} className="chip small">{k}</span>)}
        </div>
      )}

      <div className="portal-box">
        <p>
          목록키 <code>{ds.portal.listKey}</code> · {ds.portal.orgName} · 목록 기준{' '}
          {ds.portal.listBaseDate} · 분석 기준 {ds.portal.analyzedAt?.slice(0, 10)}
        </p>
        {ds.portal.listUrl && (
          <a className="portal-link" href={ds.portal.listUrl} target="_blank" rel="noreferrer">
            공공데이터포털에서 원문 확인 ↗
          </a>
        )}
        <p className="evidence-note">
          근거 수준: 목록 메타데이터만(CATALOG_METADATA_ONLY) — 실제 데이터 내용은 확인되지 않았습니다.
        </p>
      </div>
    </div>
  )
}

function Prop({ k, v }) {
  return (
    <div className="prop">
      <span className="prop-k">{k}</span>
      <span className="prop-v">{v}</span>
    </div>
  )
}

/* 데이터 구조 탭(v1.2) — 실제 파일에서 관측한 원본 컬럼·유형·예시값 상태.
   미수집·보류는 오류가 아닌 정상 상태로 표시한다. */
function StructureView({ st }) {
  const label = COVERAGE_LABEL[st.coverageStatus] || st.coverageStatus
  if (!st.assets) {
    return (
      <div className="structure-view">
        <p className={`coverage-note s-${st.coverageStatus}`}>
          {label}
          {st.coverageStatus === 'NOT_COLLECTED' &&
            ' — 품질 문제가 아니라 수집 순번입니다.'}
        </p>
        {st.portalUrl && (
          <p><a href={st.portalUrl} target="_blank" rel="noreferrer">공공데이터포털에서 원문 확인 ↗</a></p>
        )}
      </div>
    )
  }
  return (
    <div className="structure-view">
      <p className="coverage-note">
        <strong>{label}</strong> · 파일 {st.coverage.availableAssets}/{st.coverage.totalAssets}개 관측
        {!st.examplesPublic && <span className="ex-policy"> · 예시값 비공개(법적 확인 전)</span>}
      </p>
      {st.assets.map((a, i) => (
        <div className="structure-asset" key={i}>
          <h3>
            {a.containerName ? `${a.containerName} › ` : ''}{a.fileName}
            <small> {a.shape || a.format} · {a.status}</small>
          </h3>
          {a.observation && (
            <p className="obs-meta">
              관측 {a.observation.observedAt?.slice(0, 10)} · {a.observation.provenance}
              {' · '}스캔 {a.observation.scanScope}
              {a.observation.licenseGate === 'COLUMNS_ONLY' && ' · 예시값 라이선스 보류'}
            </p>
          )}
          {(a.tables || []).map((t) => (
            <div key={t.tableIndex}>
              {t.sheetName && <p className="sheet-name">시트: {t.sheetName}</p>}
              <div className="table-scroll">
                <table className="structure-table">
                  <thead>
                    <tr><th>#</th><th>원본 컬럼명</th><th>관측 유형</th><th>고유값</th><th>예시값</th></tr>
                  </thead>
                  <tbody>
                    {t.columns.map((c) => (
                      <tr key={c.ordinal}>
                        <td>{c.ordinal}</td>
                        <td>{c.sourceName}</td>
                        <td>{c.observedType || '—'}</td>
                        <td>{c.distinctCount != null ? c.distinctCount.toLocaleString() + (c.distinctApprox ? '≈' : '') : '—'}</td>
                        <td>
                          {c.examples
                            ? c.examples.slice(0, 3).join(', ')
                            : <em className="ex-status">{EXAMPLE_STATUS_LABEL[c.exampleStatus] || (c.exampleStatus === 'AVAILABLE' ? '비공개(정책)' : c.exampleStatus)}</em>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="table-meta">행 {t.rowsScanned?.toLocaleString() ?? '—'} · 컬럼 {t.columnCount} · 범위 {t.scanScope}</p>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
