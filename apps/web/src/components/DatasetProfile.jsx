import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import WarningPanel from './WarningPanel.jsx'
import EvidenceRow from './EvidenceRow.jsx'
import CoverageIndicator from './CoverageIndicator.jsx'
import PossibleUsesLens from './PossibleUsesLens.jsx'

/* 상세 = 렌즈 5종(§5.1). 기술 표현(정규화·원본·JSON-LD)은 접힘 격리였다가
   2026-08-04 '원본 데이터' 렌즈로 승격 — 한 번의 클릭으로 도달하게 한다.
   라벨은 labels.js LENS_LABEL. */
const LENS_IDS = ['overview', 'structure', 'evidence', 'uses', 'raw']

export default function DatasetProfile({
  recordId, lens = 'overview', onLensChange, onClose, onOpen, planAvailable,
}) {
  const { t, L } = useLang()
  // v1.5 게이팅(P0): 구버전 서버에는 활용 초안 렌즈를 노출하지 않는다.
  // 딥링크(?lens=uses)는 시도를 허용하고 오류 문안으로 강등한다.
  const lenses = (planAvailable ? LENS_IDS : LENS_IDS.filter((l) => l !== 'uses'))
    .map((l) => [l, L.LENS_LABEL[l]])
  const [cardBody, setCardBody] = useState(null)
  const [structBody, setStructBody] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setCardBody(null)
    setStructBody(null)
    setError(null)
    api.dataset(recordId, 'card').then(setCardBody).catch((e) => setError(e.message))
  }, [recordId])

  useEffect(() => {
    if (lens !== 'structure' || structBody) return
    api.structure(recordId).then(setStructBody).catch((e) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lens, recordId])

  // drawer 접근성(§8.2): dialog 시맨틱 + Escape + 포커스 트랩 + 닫을 때 포커스 복귀
  const asideRef = useRef(null)
  const closeRef = useRef(onClose)
  closeRef.current = onClose
  useEffect(() => {
    const prev = document.activeElement
    const aside = asideRef.current
    aside?.querySelector('.close')?.focus()
    const onKey = (e) => {
      if (e.key === 'Escape') { closeRef.current(); return }
      if (e.key !== 'Tab' || !aside) return
      const els = aside.querySelectorAll(
        'a[href], button:not([disabled]), input, select, textarea, summary, [tabindex]:not([tabindex="-1"])',
      )
      if (!els.length) return
      const first = els[0]
      const last = els[els.length - 1]
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      prev?.focus?.()
    }
  }, [])

  // 렌즈 탭 ARIA(§8.2): tab/aria-selected/화살표 키 이동
  const onTabKey = (e, idx) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return
    e.preventDefault()
    const next = (idx + (e.key === 'ArrowRight' ? 1 : -1) + lenses.length) % lenses.length
    onLensChange?.(lenses[next][0])
    e.currentTarget.parentElement.children[next]?.focus()
  }

  const ds = cardBody?.data?.dataset
  const body = lens === 'structure' ? structBody : cardBody
  const activeLens = lenses.some(([l]) => l === lens) ? lens : 'overview'

  // 좁은 화면에서 탭 행은 가로 스크롤 — 활성 탭이 스크롤 밖에 있지 않게 한다(딥링크 진입 포함)
  useEffect(() => {
    asideRef.current
      ?.querySelector('.drawer-tabs .tab.active')
      ?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  }, [activeLens])

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside
        className="drawer"
        ref={asideRef}
        role="dialog"
        aria-modal="true"
        aria-label={ds ? t('profile.aria', { title: ds.title }) : t('profile.ariaFallback')}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-head">
          <div className="drawer-nav">
            <div className="drawer-tabs" role="tablist" aria-label={t('profile.lensAria')}>
              {lenses.map(([l, label], i) => (
                <button
                  key={l}
                  role="tab"
                  aria-selected={activeLens === l}
                  tabIndex={activeLens === l ? 0 : -1}
                  className={activeLens === l ? 'tab active' : 'tab'}
                  onClick={() => onLensChange?.(l)}
                  onKeyDown={(e) => onTabKey(e, i)}
                >
                  {label}
                </button>
              ))}
            </div>
            {/* 원본 접근은 핵심 행동(P1) — 렌즈 무관, 탭과 같은 행에서 한 번에 도달.
                탭이 아니라 외부 링크이므로 tablist 밖에 둔다. 이 서비스는 재배포하지 않는다.
                라벨은 목록 행과 동일('포털 원문') — '원본 데이터' 렌즈와 구분한다 */}
            {ds?.portalUrl && (
              <a className="tab tab-link" href={ds.portalUrl} target="_blank" rel="noreferrer">
                {t('profile.portalTab')}
              </a>
            )}
          </div>
          <button className="close" onClick={onClose} aria-label={t('profile.close')}>✕</button>
        </div>

        {error && <p className="error">{error}</p>}
        {!body && !error && <p className="loading">{t('common.loading')}</p>}

        {activeLens !== 'uses' && <WarningPanel warnings={body?.warnings} notices={body?.notices} />}

        {ds && activeLens === 'overview' && <OverviewLens ds={ds} />}
        {activeLens === 'structure' && structBody && <StructureView st={structBody.data} />}
        {ds && activeLens === 'evidence' && <EvidenceLens ds={ds} meta={cardBody.meta} />}
        {ds && activeLens === 'uses' && <PossibleUsesLens ds={ds} onOpen={onOpen} />}
        {ds && activeLens === 'raw' && <RawLens recordId={recordId} />}

        {/* 판정 스냅샷은 L1에 유지(신뢰 신호), 규칙 버전 원문은 근거 렌즈로 이동(P1) */}
        {body && (
          <p className="drawer-meta">{t('profile.meta', { s: body.meta.sourceSnapshot })}</p>
        )}
      </aside>
    </div>
  )
}

function OverviewLens({ ds }) {
  const { t, L } = useLang()
  const fresh = L.FRESHNESS_LABEL[ds.freshness?.status] || L.FRESHNESS_LABEL.UNKNOWN
  return (
    <div className="profile">
      <h2>
        <span className={`type type-${ds.listType}`}>{ds.listType}</span> {ds.title}
      </h2>
      <p className="org">{ds.orgName}</p>

      <div className="prop-grid">
        <Prop k={t('profile.k.theme')} v={ds.theme?.top ? `${ds.theme.top}${ds.theme.sub ? ' › ' + ds.theme.sub : ''}` : '—'} />
        <Prop k={t('profile.k.formats')} v={ds.formats?.join(', ') || '—'} />
        <Prop k={t('profile.k.cycle')} v={ds.updateCycleRaw || '—'} />
        <Prop k={t('profile.k.license')} v={ds.license?.raw || '—'} />
        <Prop k={t('profile.k.created')} v={ds.createdDate || '—'} />
        <Prop k={t('profile.k.modified')} v={ds.modifiedDate || '—'} />
        <Prop k={t('profile.k.spatial')} v={ds.spatial || t('profile.notListed')} />
        <Prop k={t('profile.k.temporal')} v={ds.temporal || t('profile.notListed')} />
        {ds.rowCount != null && <Prop k={t('profile.k.rows')} v={ds.rowCount.toLocaleString()} />}
        {ds.apiType && <Prop k={t('profile.k.apiType')} v={ds.apiType} />}
      </div>

      <div className="judgments">
        <span
          className="completeness large"
          title={t('profile.completenessTitle', { profile: ds.completeness.profile, rule: ds.completeness.rule })}
        >
          {t('profile.filled', { total: ds.completeness.totalFields, filled: ds.completeness.filledFields })}
          <small>
            {t('profile.filledDetail', {
              profile: ds.completeness.profile, typical: ds.completeness.typical,
              share: ds.completeness.typicalShare, top: ds.completeness.topPercent,
            })}
          </small>
        </span>
        <span className={`freshness ${fresh.cls}`} title={ds.freshness?.note || ''}>
          {fresh.text}
          {ds.freshness?.ageDays != null && <small>{t('profile.ageDays', { n: ds.freshness.ageDays })}</small>}
        </span>
      </div>

      {ds.completeness.fields && (
        <div className="field-checklist">
          {Object.entries(ds.completeness.fields).map(([f, filled]) => (
            <span key={f} className={filled ? 'fc filled' : 'fc missing'}>
              {filled ? '✓' : '—'} {L.COMPLETENESS_FIELD_LABEL[f] || f}
            </span>
          ))}
        </div>
      )}

      {ds.description && (
        <>
          <h3>{t('profile.descTitle')} <small className="desc-src">{t('profile.descSrc')}</small></h3>
          {ds.description.length > 220 ? (
            /* 긴 원문은 접는다(P1) — 서비스가 요약을 생성하지는 않는다(§8 언어 규칙) */
            <details className="desc-fold">
              <summary>{ds.description.slice(0, 160)}…</summary>
              <p className="desc">{ds.description}</p>
            </details>
          ) : (
            <p className="desc">{ds.description}</p>
          )}
        </>
      )}
      {ds.dataLimits && (
        <>
          <h3>{t('profile.limitsTitle')}</h3>
          <p className="desc">{ds.dataLimits}</p>
        </>
      )}
      {ds.keywords?.length > 0 && (
        <div className="keywords">
          <span className="examples-label">{t('profile.keywordsLabel')}</span>
          {ds.keywords.map((k) => <span key={k} className="chip small">{k}</span>)}
        </div>
      )}

      <div className="portal-box">
        <p>
          {t('profile.portalBox', {
            listKey: ds.portal.listKey, org: ds.portal.orgName,
            base: ds.portal.listBaseDate, analyzed: ds.portal.analyzedAt?.slice(0, 10),
          })}
        </p>
        {ds.portal.listUrl && (
          <a className="portal-link" href={ds.portal.listUrl} target="_blank" rel="noreferrer">
            {t('profile.portalLink')}
          </a>
        )}
        <EvidenceRow level={ds.evidenceLevel} />
      </div>
    </div>
  )
}

/* 근거 렌즈(§5.4) — 신규 필드 없이 기존 값 조합. "판정이 있으면 근거가 있다"의 구현. */
function EvidenceLens({ ds, meta }) {
  const { t, L } = useLang()
  return (
    <div className="profile">
      <h2>{t('profile.evTitle')}</h2>
      <EvidenceRow level={ds.evidenceLevel} snapshot={meta.sourceSnapshot} />
      <div className="prop-grid">
        <Prop k={t('profile.k.snapshot')} v={t('profile.snapshotV', { s: meta.sourceSnapshot, p: meta.processedAt?.slice(0, 10) })} />
        <Prop k={t('profile.k.schema')} v={meta.schemaVersion} />
      </div>
      {ds.freshness?.note && <p className="obs-meta">{t('profile.freshNote', { note: ds.freshness.note })}</p>}
      {/* 규칙 버전 원문은 L3(P1) — 존재는 보이되 기본 접힘 */}
      <details className="raw-section">
        <summary>{t('profile.rulesSummary')}</summary>
        <div className="prop-grid">
          <Prop k={t('profile.k.rules')} v={meta.ruleVersions.join(', ') || '—'} />
          <Prop k={t('profile.k.cardRule')} v={ds.cardRule || '—'} />
          <Prop k={t('profile.k.completenessRule')} v={t('profile.completenessRuleV', { rule: ds.completeness.rule, profile: ds.completeness.profile })} />
          <Prop k={t('profile.k.freshRule')} v={ds.freshness?.rule || '—'} />
        </div>
      </details>
      {ds.regions?.length > 0 && (
        <>
          <h3>{t('profile.regionTitle')}</h3>
          <ul className="case-list">
            {ds.regions.map((r) => (
              <li key={r.code}>
                {t('profile.regionItem', {
                  name: r.name, label: L.EVIDENCE_LABEL[r.evidence] || r.evidence,
                  code: r.evidence, conf: r.confidence,
                })}
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="obs-meta">{t('profile.provNote')}</p>
    </div>
  )
}

/* 원본 데이터 렌즈 — 기술 표현(정규화 · 원본 · JSON-LD). 판정을 덧붙이지 않고
   서버 표현을 그대로 보여 준다(불변식 3). 구 접힘 영역(§5.6)의 승격. */
function RawLens({ recordId }) {
  const { t, L } = useLang()
  const [view, setView] = useState('normalized')
  const [body, setBody] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    setBody(null)
    setError(null)
    api.dataset(recordId, view).then(setBody).catch((e) => setError(e.message))
  }, [view, recordId])
  return (
    <div className="profile raw-lens">
      <h2>{t('profile.rawTitle')}</h2>
      <div className="raw-tabs">
        {Object.entries(L.RAW_VIEW_LABEL).map(([v, label]) => (
          <button
            key={v}
            className={view === v ? 'tab active' : 'tab'}
            onClick={() => setView(v)}
          >
            {label}
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      {!body && !error && <p className="loading">{t('common.loading')}</p>}
      {body && <pre className="json-view">{JSON.stringify(body.data.dataset, null, 2)}</pre>}
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

/* 데이터 구조 렌즈(§5.3) — 실제 파일에서 관측한 원본 컬럼·유형·예시값 상태.
   미수집·보류는 오류가 아닌 정상 상태로 표시한다. sourceName은 원본 그대로. */
function StructureView({ st }) {
  const { t, L } = useLang()
  if (!st.assets) {
    return (
      <div className="structure-view">
        <CoverageIndicator status={st.coverageStatus} />
        {st.portalUrl && (
          <p><a href={st.portalUrl} target="_blank" rel="noreferrer">{t('profile.portalLink')}</a></p>
        )}
      </div>
    )
  }
  return (
    <div className="structure-view">
      <CoverageIndicator
        status={st.coverageStatus}
        available={st.coverage.availableAssets}
        total={st.coverage.totalAssets}
        examplesPublic={st.examplesPublic}
      />
      {st.assets.map((a, i) => (
        <div className="structure-asset" key={i}>
          <h3>
            {a.containerName ? `${a.containerName} › ` : ''}{a.fileName}
            <small> {a.shape || a.format} · {a.status}</small>
          </h3>
          {a.failureReason && <p className="obs-meta">{t('profile.failReason', { r: a.failureReason })}</p>}
          <EvidenceRow className="obs-meta" observation={a.observation}>
            {a.observation?.licenseGate === 'COLUMNS_ONLY' && t('profile.licenseGate')}
          </EvidenceRow>
          {(a.tables || []).map((tb) => (
            <div key={tb.tableIndex}>
              {tb.sheetName && <p className="sheet-name">{t('profile.sheet', { s: tb.sheetName })}</p>}
              <div className="table-scroll" tabIndex={0}>
                <table className="structure-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>{t('profile.th.source')}</th>
                      <th>{t('profile.th.type')}</th>
                      <th>{t('profile.th.distinct')}</th>
                      <th>{t('profile.th.examples')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tb.columns.map((c) => (
                      <tr key={c.ordinal}>
                        <td>{c.ordinal}</td>
                        <td>
                          {c.sourceName}
                          {c.note && <small className="col-note"> — {c.note}</small>}
                        </td>
                        <td>{c.observedType || '—'}</td>
                        <td>{c.distinctCount != null ? c.distinctCount.toLocaleString() + (c.distinctApprox ? '≈' : '') : '—'}</td>
                        <td>
                          {c.examples
                            ? c.examples.slice(0, 3).join(', ')
                            : <em className="ex-status">{L.exampleStatusLabel(c.exampleStatus, st.examplesPublic)}</em>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="table-meta">
                {t('profile.tableMeta', {
                  scanned: tb.rowsScanned?.toLocaleString() ?? '—',
                  observed: tb.rowCountObserved != null ? tb.rowCountObserved.toLocaleString() : null,
                  cols: tb.columnCount, scope: tb.scanScope,
                })}
              </p>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
