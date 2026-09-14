import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import WarningPanel from './WarningPanel.jsx'
import { rowButtonProps } from '../a11y.js'

export default function ChangesView({ onOpen }) {
  const { t, L } = useLang()
  const [status, setStatus] = useState('')
  const [body, setBody] = useState(null)
  const [items, setItems] = useState([])
  const [error, setError] = useState(null)

  const statuses = [['', t('changes.all')], ...Object.entries(L.CHANGE_STATUS_LABEL)]

  const load = (cursor = null, st = status) => {
    api
      .changes({ status: st || undefined, cursor: cursor || undefined, pageSize: 50 })
      .then((b) => {
        setBody(b)
        setItems((prev) => (cursor ? [...prev, ...b.data.items] : b.data.items))
      })
      .catch((e) => setError(`${e.code || ''} ${e.message}`))
  }

  useEffect(() => {
    load(null, status)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status])

  return (
    <section>
      <div className="filters">
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          {statuses.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        {body?.data.baseSnapshot && (
          <span className="result-meta">
            {t('changes.base', { b: body.data.baseSnapshot, c: body.data.currentSnapshot })}
          </span>
        )}
      </div>

      {error && <p className="error">{error}</p>}
      <WarningPanel warnings={body?.warnings} notices={body?.notices} />

      {/* v1.6: 상태별 집계 — 무엇이 얼마나 바뀌었는지 한 줄 요약 */}
      {body?.data?.summary && Object.keys(body.data.summary).length > 0 && (
        <p className="result-meta">
          {t('changes.summary')}
          {Object.entries(body.data.summary)
            .map(([s, n]) => t('changes.count', { label: L.CHANGE_STATUS_LABEL[s] || s, n: n.toLocaleString() }))
            .join(' · ')}
        </p>
      )}

      {/* 기준 부재는 사유 코드(v1.6)로 판별 — 문자열 결합 폴백은 구버전 응답용 */}
      {body && body.data.totalEstimate === 0
        && !(body.data.baseUnavailableReason
          ?? body.warnings.some((w) => w.includes('이전 스냅샷'))) && (
        <p className="empty">{t('changes.empty')}</p>
      )}

      <ul className="results">
        {items.map((c) => (
          <li key={`${c.status}-${c.recordId}`} className="result-row">
            <div className="row-main" {...rowButtonProps(() => onOpen(c.recordId))}>
              <div className="row-title">
                <span className={`change-status s-${c.status}`} title={L.CHANGE_STATUS_NOTE[c.status] || ''}>
                  {L.CHANGE_STATUS_LABEL[c.status] || c.status}
                </span>
                <strong>{c.title}</strong>
              </div>
              <div className="row-sub">
                <span>{c.orgName}</span>
                {c.changedFields && <span>{t('changes.fields', { f: c.changedFields.join(', ') })}</span>}
              </div>
            </div>
          </li>
        ))}
      </ul>

      {body?.data.hasMore && (
        <button className="more" onClick={() => load(body.data.nextCursor)}>{t('changes.more')}</button>
      )}
    </section>
  )
}
