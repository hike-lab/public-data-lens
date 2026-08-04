import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { cycleLabel, licenseLabel, COMPARE_FIELD_LABEL } from '../labels.js'
import WarningPanel from './WarningPanel.jsx'

function fmt(v, field) {
  if (v === null || v === undefined) return '—'
  if (Array.isArray(v)) return v.length ? v.join(', ') : '—'
  if (field === 'updateCycle') return cycleLabel(String(v))
  if (field === 'license') return licenseLabel(String(v))
  return String(v)
}

export default function CompareView({ ids, onRemove, onOpen }) {
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
        <p>검색 탭에서 데이터셋을 2~5개 선택하면 구조화된 사실 비교를 보여줍니다.</p>
        {ids.length === 1 && <p>현재 1개 선택됨 — 1개 더 선택하세요.</p>}
      </section>
    )
  }

  const datasets = body?.data?.datasets || []

  return (
    <section>
      {error && <p className="error">{error}</p>}
      <WarningPanel warnings={body?.warnings} notices={body?.notices} />
      {!body && !error && <p className="loading">비교 중…</p>}
      {body && (
        <>
          <p className="result-meta">{body.data.note}</p>
          <div className="table-wrap">
            <table className="compare-table">
              <thead>
                <tr>
                  <th>항목</th>
                  {datasets.map((d) => (
                    <th key={d.recordId}>
                      <button className="link" onClick={() => onOpen(d.recordId)}>
                        {d.title}
                      </button>
                      <div className="th-sub">
                        <span className={`type type-${d.listType}`}>{d.listType}</span>
                        <button className="remove" onClick={() => onRemove(d.recordId)}>
                          제외
                        </button>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {body.data.differences.map((diff) => (
                  <tr key={diff.field} className="diff">
                    <td>{COMPARE_FIELD_LABEL[diff.field] || diff.field}</td>
                    {datasets.map((d) => (
                      <td key={d.recordId}>{fmt(diff.values[d.recordId], diff.field)}</td>
                    ))}
                  </tr>
                ))}
                {showShared &&
                  body.data.sharedFields.map((s) => (
                    <tr key={s.field} className="shared">
                      <td>{COMPARE_FIELD_LABEL[s.field] || s.field}</td>
                      <td colSpan={datasets.length}>{fmt(s.value, s.field)} (공통)</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <button className="more" onClick={() => setShowShared((v) => !v)}>
            {showShared ? '공통 항목 접기' : `공통 항목 ${body.data.sharedFields.length}개 보기`}
          </button>
        </>
      )}

      {body?.data?.structureComparison && (
        <div className="structure-compare">
          <h3>원본 컬럼 구조 비교</h3>
          <p className="obs-meta">{body.data.structureComparison.note}</p>
          <p>
            <strong>공통 컬럼 {body.data.structureComparison.commonColumns.length}개:</strong>{' '}
            {body.data.structureComparison.commonColumns.join(', ') || '없음'}
          </p>
          {Object.entries(body.data.structureComparison.onlyIn).map(([rid, cols]) => {
            // recordId를 그대로 노출하지 않는다 — datasets[]의 제목으로 해소(§6)
            const title = body.data.datasets.find((d) => d.recordId === rid)?.title || rid
            return (
              <p key={rid}>
                <strong>{title}에만:</strong> {cols.length ? cols.join(', ') : '없음'}
                {' '}(전체 {body.data.structureComparison.columnCounts[rid]}개)
              </p>
            )
          })}
        </div>
      )}
    </section>
  )
}
