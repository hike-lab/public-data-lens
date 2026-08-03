import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function CasesView({ onOpen }) {
  const [list, setList] = useState(null)
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/cases').then((r) => r.json()).then(setList).catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!selected) return
    setDetail(null)
    fetch(`/api/cases/${selected}`).then((r) => r.json()).then(setDetail).catch((e) => setError(e.message))
  }, [selected])

  if (error) return <p className="error">{error}</p>
  if (!list) return <p className="loading">불러오는 중…</p>
  if (!list.data?.items) return <p className="error">사례 API 응답이 올바르지 않습니다 (서버 버전 확인 필요)</p>

  if (!selected) {
    return (
      <section>
        <p className="result-meta">
          목적 질의 → 후보 선정 → 한계 확인의 절차를 보여주는 사전 계산 사례입니다.
          후보 데이터셋 카드는 현재 스냅샷 기준으로 재조회됩니다.
        </p>
        <ul className="results">
          {list.data.items.map((c) => (
            <li key={c.id} className="card-row">
              <div className="card-main" onClick={() => setSelected(c.id)}>
                <div className="card-title-line">
                  <span className="type type-STD">사례</span>
                  <strong>{c.title}</strong>
                </div>
                <div className="card-sub">
                  <span>{c.purpose}</span>
                </div>
                <div className="card-badges">
                  <span className="chip small">후보 {c.candidateCount}개</span>
                  <span className="chip small">작성 스냅샷 {c.sourceSnapshot}</span>
                  {!c.humanReviewed && <span className="region inferred">인간 검토 전</span>}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    )
  }

  if (!detail) return <p className="loading">불러오는 중…</p>
  const d = detail.data

  return (
    <section>
      <button className="link" onClick={() => setSelected(null)}>← 사례 목록</button>
      <h2 style={{ margin: '10px 0 2px' }}>{d.title}</h2>
      <p className="result-meta">{d.purpose}</p>
      {detail.warnings.filter((w) => !w.startsWith('본 결과는')).map((w, i) => (
        <p className="warning" key={i}>⚠ {w}</p>
      ))}

      <h3 className="case-h">① 목적 분해</h3>
      <ul className="case-list">{d.purposeBreakdown.map((x, i) => <li key={i}>{x}</li>)}</ul>

      <h3 className="case-h">② 후보 데이터셋 (선정 이유는 목록 사실 기반)</h3>
      <ul className="results">
        {d.candidates.map((c) => (
          <li key={c.recordId} className="card-row">
            <div className="card-main" onClick={() => c.presentInCurrentSnapshot && onOpen(c.recordId)}>
              <div className="card-title-line">
                {c.card && <span className={`type type-${c.card.listType}`}>{c.card.listType}</span>}
                <strong>{c.card ? c.card.title : c.recordId}</strong>
                <span className="chip small">{c.role}</span>
              </div>
              <div className="card-sub"><span>{c.whySelected}</span></div>
              {c.card && (
                <div className="card-badges">
                  <span className="completeness">
                    <span className="bar"><span className="fill" style={{ width: `${c.card.completeness.score * 100}%` }} /></span>
                    {(c.card.completeness.score * 100).toFixed(0)}% ({c.card.completeness.profile})
                  </span>
                  {c.card.modifiedDate && <span className="chip small">수정 {c.card.modifiedDate}</span>}
                </div>
              )}
              {!c.presentInCurrentSnapshot && <p className="warning">현재 스냅샷에 없음 — 재검증 필요</p>}
            </div>
            {c.card?.portalUrl && (
              <div className="card-actions">
                <a href={c.card.portalUrl} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>포털 원문 ↗</a>
              </div>
            )}
          </li>
        ))}
      </ul>

      <h3 className="case-h">③ 함께 필요한 데이터</h3>
      <ul className="case-list">
        {d.complementaryData.map((x, i) => <li key={i}><strong>{x.need}</strong> — {x.how}</li>)}
      </ul>

      <h3 className="case-h">④ 예상 결합 키 (추론 — 비단정)</h3>
      <ul className="case-list">
        {d.expectedJoinKeys.map((x, i) => <li key={i}><strong>{x.key}</strong> — {x.note}</li>)}
      </ul>

      <h3 className="case-h">⑤ 미확인 항목</h3>
      <ul className="case-list">{d.unverified.map((x, i) => <li key={i}>{x}</li>)}</ul>

      <h3 className="case-h">⑥ 한계</h3>
      <ul className="case-list">{d.limitations.map((x, i) => <li key={i}>{x}</li>)}</ul>

      <div className="portal-box" style={{ marginTop: 16 }}>
        <p>
          재현성 메타데이터: 작성일 {d.metadata.createdAt} · 작성 스냅샷 {d.metadata.sourceSnapshot} ·
          현재 스냅샷 {d.currentSnapshot} · Prompt {d.metadata.promptVersion} · 모델 {d.metadata.model} ·
          인간 검토 {d.metadata.humanReviewed ? '완료' : '전'}
        </p>
        <details>
          <summary>Tool 호출 기록 ({d.toolTrace.length}건)</summary>
          <ul className="case-list">
            {d.toolTrace.map((t, i) => (
              <li key={i}><code>{t.tool}</code> {JSON.stringify(t.args)} → {t.resultSummary}</li>
            ))}
          </ul>
        </details>
      </div>
    </section>
  )
}
