import { useState } from 'react'

const MCP_URL = `${window.location.origin}/projects/public-data-lens/mcp`

const EXAMPLE_PROMPTS = [
  '폐교 활용 사업을 검토 중인데 참고할 공공데이터 찾아줘',
  '고령자 의료 접근성 분석에 쓸 데이터 후보를 비교해줘',
  '위도·경도 컬럼이 실제로 있는 관광 데이터만 골라줘',
]

export default function ConnectView() {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(MCP_URL)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch { /* 수동 복사 */ }
  }

  return (
    <section className="about connect">
      <div className="about-hero">
        <h2>AI에서 대화로 공공데이터를 탐색하세요</h2>
        <p>
          이 서비스의 검색·비교·구조 조회는 <strong>MCP(Model Context Protocol)</strong> 서버로
          제공됩니다. MCP를 지원하는 AI에 아래 주소를 등록하면 화면 대신 대화로 탐색할 수
          있습니다 — 인증 없이 무료이며, 웹과 동일한 판정 엔진이라 근거 수준과 규칙 버전이
          응답에 함께 담깁니다.
        </p>
      </div>

      <div className="mcp-url">
        <code>{MCP_URL}</code>
        <button onClick={copy}>{copied ? '복사됨 ✓' : '복사'}</button>
      </div>

      <h3>클라이언트별 등록 방법</h3>
      <div className="connect-grid">
        <div className="connect-card">
          <h4>Claude 웹 · 앱</h4>
          <ol className="mcp-steps">
            <li><strong>설정 → 커넥터 → 커스텀 커넥터 추가</strong></li>
            <li>위 주소를 붙여넣고 추가</li>
            <li>대화에서 바로 질문 — 정형화된 활용 계획은 프롬프트 메뉴의 <code>build_data_plan</code></li>
          </ol>
        </div>
        <div className="connect-card">
          <h4>Claude Code (터미널)</h4>
          <pre className="connect-code">claude mcp add --transport http \{'\n'}  public-data-lens {MCP_URL}</pre>
        </div>
        <div className="connect-card">
          <h4>기타 MCP 클라이언트</h4>
          <p className="connect-note">
            원격 MCP(streamable HTTP)를 지원하는 클라이언트라면 같은 주소로 등록할 수 있습니다.
            명세: <a href="/projects/public-data-lens/spec/tools/1.0" target="_blank" rel="noreferrer">Tool 스키마(JSON)</a>
          </p>
        </div>
      </div>

      <h3>이렇게 물어보세요</h3>
      <ul className="about-list">
        {EXAMPLE_PROMPTS.map((p) => <li key={p}><em>"{p}"</em></li>)}
      </ul>

      <h3>제공되는 도구</h3>
      <p className="connect-note">
        데이터셋 검색 · 단건 조회 · 최대 5개 비교 · 월별 변경 추적 · 카탈로그 통계 ·
        컬럼 기준 검색 · 실파일 구조 조회 · <strong>활용 계획 초안(build_data_plan)</strong> ·
        서비스 개요 — 총 9종. 목적 한 문장이면 후보 역할·선정 근거·예상 결합 항목·확인할
        한계를 계획 초안으로 받을 수 있습니다. 모든 판정에는 근거 수준과 규칙 버전이
        표기됩니다.
      </p>
    </section>
  )
}
