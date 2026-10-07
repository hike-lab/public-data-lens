import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import WarningPanel from './WarningPanel.jsx'

function fmt(v, field, L) {
  if (v === null || v === undefined) return '—'
  if (Array.isArray(v)) return v.length ? v.join(', ') : '—'
  if (field === 'updateCycle') return L.cycleLabel(String(v))
  if (field === 'license') return L.licenseLabel(String(v))
  return String(v)
}

export default function CompareView({ ids, onRemove, onOpen }) {
  const { t, L } = useLang()
  const [body, setBody] = useState(null)
  const [error, setError] = useState(null)
  const [showShared, setShowShared] = useState(false)

  useEffect(() => {
    setBody(null)
    setError(null)
    if (ids.length >= 2) {
      api.compare(ids).then(setBody).catch((e) => setError(`${e.code || ''} ${e.message}`))
    }
  }, [ids])

  if (ids.length < 2) {
    return (
      <section className="empty">
        <p>{t('compare.emptyHint')}</p>
        {ids.length === 1 && <p>{t('compare.oneSelected')}</p>}
      </section>
    )
  }

  const datasets = body?.data?.datasets || []

  return (
    <section>
      {error && <p className="error">{error}</p>}
      <WarningPanel warnings={body?.warnings} notices={body?.notices} />
      {!body && !error && <p className="loading">{t('compare.loading')}</p>}
      {body && (
        <>
          <p className="result-meta">{body.data.note}</p>
          <div className="table-wrap">
            <table className="compare-table">
              <thead>
                <tr>
                  <th>{t('compare.thField')}</th>
                  {datasets.map((d) => (
                    <th key={d.recordId}>
                      <button className="link" onClick={() => onOpen(d.recordId)}>
                        {d.title}
                      </button>
                      <div className="th-sub">
                        <span className={`type type-${d.listType}`}>{d.listType}</span>
                        <button className="remove" onClick={() => onRemove(d.recordId)}>
                          {t('compare.remove')}
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.data.differences.map((diff) => (
                  <tr key={diff.field} className="diff">
                    <td>{L.COMPARE_FIELD_LABEL[diff.field] || diff.field}</td>
                    {datasets.map((d) => (
                      <td key={d.recordId}>{fmt(diff.values[d.recordId], diff.field, L)}</td>
                    ))}
                  </tr>
                ))}
                {showShared &&
                  body.data.sharedFields.map((s) => (
                    <tr key={s.field} className="shared">
                      <td>{L.COMPARE_FIELD_LABEL[s.field] || s.field}</td>
                      <td colSpan={datasets.length}>{fmt(s.value, s.field, L)}{t('compare.shared')}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <button className="more" onClick={() => setShowShared((v) => !v)}>
            {showShared ? t('compare.sharedHide') : t('compare.sharedShow', { n: body.data.sharedFields.length })}
          </button>
        </>
      )}

      {body?.data?.structureComparison && (
        <div className="structure-compare">
          <h3>{t('compare.structTitle')}</h3>
          <p className="obs-meta">{body.data.structureComparison.note}</p>
          <p>
            <strong>{t('compare.common', { n: body.data.structureComparison.commonColumns.length })}</strong>{' '}
            {body.data.structureComparison.commonColumns.join(', ') || t('compare.none')}
          </p>
          {Object.entries(body.data.structureComparison.onlyIn).map(([rid, cols]) => {
            // recordId를 그대로 노출하지 않는다 — datasets[]의 제목으로 해소(§6)
            const title = body.data.datasets.find((d) => d.recordId === rid)?.title || rid
            return (
              <p key={rid}>
                <strong>{t('compare.onlyIn', { title })}</strong> {cols.length ? cols.join(', ') : t('compare.none')}
                {t('compare.totalCols', { n: body.data.structureComparison.columnCounts[rid] })}
              </p>
            )
          })}
        </div>
      )}
    </section>
  )
}
