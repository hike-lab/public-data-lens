// 서버 경고·오류의 단일 표시 지점(가이드 §7 — 웹·컨시어지 표면 공유).
// 서버 문안을 치환하지 않는다. 유일한 표시 정책: 상시 고지(면책·생성형 고지)는
// 푸터·결과 헤더가 상시 담당하므로 이 패널에서는 반복하지 않는다.
// v1.5 notices[]가 있으면 severity로 분기(문자열 결합 제거), 구버전 응답은 접두 폴백.
const STANDING_PREFIXES = ['본 결과는', '생성형 응답은']

export default function WarningPanel({ warnings, notices, error }) {
  const items = notices
    ? notices.filter((n) => n.severity !== 'info').map((n) => n.text)
    : (warnings || []).filter((w) => !STANDING_PREFIXES.some((p) => w.startsWith(p)))
  if (!items.length && !error) return null
  return (
    <>
      {error && <p className="error">{error}</p>}
      {items.map((w, i) => (
        <p className="notice" key={i}>{w}</p>
      ))}
    </>
  )
}
