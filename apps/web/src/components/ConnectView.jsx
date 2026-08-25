import { useState } from 'react'

// 정본 URI(§7 영구 불변)를 안내한다 — 화면 origin을 쓰면 dev·프리뷰에서
// 동작하지 않는 로컬 주소가 복사된다(P0). 정본은 배포 후 변경 불가이므로 상수가 맞다.
const MCP_URL = 'https://service.datahub.kr/projects/public-data-lens/mcp'

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
        <h2>웹에서 제공하는 데이터 탐색 기능을 AI에서도 사용할 수 있습니다</h2>
        <p>
          공공데이터 렌즈의 검색·비교·구조 확인 기능은 <strong>MCP(Model Context Protocol)</strong>
          서버로도 제공됩니다. MCP를 지원하는 AI에 아래 주소를 등록하면 대화로 데이터를
          탐색할 수 있습니다. 인증 없이 무료로 이용할 수 있으며, 웹과 같은 기준을 사용하므로
          확인 근거와 적용한 규칙 버전도 함께 표시됩니다.
        </p>
      </div>

      <div className="mcp-url">
        <code>{MCP_URL}</code>
        <button onClick={copy}>{copied ? '복사됨 ✓' : '복사'}</button>
      </div>

      {/* capability demonstration — 설치 안내보다 먼저, 무엇이 달라지는지(§3 #7).
          결과를 날조하지 않는다: 단계는 실제 Tool 파이프라인, 응답 항목은 계약 필드다 */}
      <h3>연결하면 이렇게 이용할 수 있습니다</h3>
      <div className="cap-demo">
        <div className="cap-col">
          <h4>말로 요청하기</h4>
          <p className="cap-quote">
            “전기차 충전소 중 위도·경도가 실제로 있고, 지역별 비교에 쓸 만한 데이터를 찾아줘”
          </p>
        </div>
        <div className="cap-col">
          <h4>렌즈가 단계별로 탐색하기</h4>
          <ol className="cap-steps">
            <li>목적 파악 <code>build_data_plan</code></li>
            <li>필요한 컬럼 검색 <code>search_by_columns</code></li>
            <li>후보 비교 <code>compare_datasets</code></li>
            <li>실제 구조 확인 <code>get_dataset_structure</code></li>
          </ol>
        </div>
        <div className="cap-col">
          <h4>근거와 함께 결과 확인하기</h4>
          <ul className="cap-out">
            <li>후보 데이터와 예상 역할 — 확정된 결과가 아니라 먼저 검토할 대상입니다</li>
            <li>좌표 컬럼을 실제 파일에서 확인한 근거(<code>FILE_OBSERVATION</code>)</li>
            <li>한계와 확인하지 못한 항목(<code>NOT_ASSESSED</code>·<code>CANDIDATE_ONLY</code>)</li>
            <li>적용한 규칙 버전과 데이터 스냅샷</li>
          </ul>
        </div>
      </div>

      <h3>AI 서비스별 연결 방법</h3>
      {/* 카드 3열은 정보량 불균형으로 폐기(P2) — 같은 구조의 아코디언으로 */}
      <div className="connect-acc">
        <details open>
          <summary>Claude 웹·앱</summary>
          <ol className="mcp-steps">
            <li>웹(claude.ai)에서 <strong>설정 → 커넥터 → 커스텀 커넥터 추가</strong></li>
            <li>위 주소를 붙여넣고 추가</li>
            <li>대화에서 바로 질문 — 정형화된 활용 계획은 프롬프트 메뉴의 <code>build_data_plan</code></li>
            <li>연결을 확인하려면 이렇게 물어보세요: “이 커넥터로 공공데이터 카탈로그 현황을 알려줘”</li>
          </ol>
          <p className="connect-note connect-caveat">
            Team·Enterprise 계정에서는 구성원 설정에 커넥터 추가 메뉴가 보이지 않을 수
            있습니다. 이 경우 조직 관리자가 먼저 커넥터를 추가해야 하며, 구성원은
            <strong>설정 → 커넥터</strong>에서 ‘연결’을 눌러 활성화할 수 있습니다. 데스크톱
            앱에서는 아래 안내에 따라 Claude Code에 등록한 뒤
            <strong> 설정 → 커넥터</strong>에서 활성화할 수도 있습니다.
          </p>
          <p className="connect-note">
            처음 사용할 때 Claude가 도구 호출마다 허용 여부를 묻는 것은 정상입니다.
            허용 창에서 <strong>‘항상 허용’</strong>을 선택하면 이후에는 다시 묻지 않습니다.
            이 서버의 도구는 모두 읽기 전용으로, 데이터를 추가·수정·삭제하지 않습니다.
          </p>
        </details>
        <details>
          <summary>Claude Code(터미널)</summary>
          <pre className="connect-code">{`claude mcp add \\
  --transport http \\
  public-data-lens \\
  ${MCP_URL}`}</pre>
          <p className="connect-note">연결 확인: <code>claude mcp list</code>에서 connected 표시</p>
        </details>
        <details>
          <summary>ChatGPT 웹</summary>
          <ol className="mcp-steps">
            <li><strong>설정 → 보안 및 로그인 → 개발자 모드</strong> 켜기</li>
            <li><a href="https://chatgpt.com/plugins" target="_blank" rel="noreferrer">ChatGPT Plugins</a> → <code>+</code> 선택</li>
            <li>
              다음 정보로 MCP 앱 등록:
              <table className="connect-table">
                <tbody>
                  <tr><th>이름</th><td>공공데이터 렌즈</td></tr>
                  <tr><th>설명</th><td>한국 공공데이터를 목적·키워드·컬럼 기준으로 검색하고 구조와 근거를 확인합니다.</td></tr>
                  <tr><th>연결</th><td>Public endpoint</td></tr>
                  <tr><th>MCP 서버 URL</th><td><code>{MCP_URL}</code></td></tr>
                  <tr><th>인증</th><td>No Authentication</td></tr>
                </tbody>
              </table>
            </li>
            <li>생성 후 탐지된 도구 목록 확인</li>
            <li>새 대화 → 입력창의 <code>+</code> → 개발자 모드 → 공공데이터 렌즈 선택</li>
            <li>대화에서 바로 질문</li>
          </ol>
          <p className="connect-note">
            연결 확인: "공공데이터 렌즈를 사용해서 공공데이터 카탈로그 현황을 알려줘."<br />
            활용 계획 작성: "공공데이터 렌즈를 사용해서 전기차 충전소 분석에 필요한 데이터
            활용 계획을 만들어줘."
          </p>
          <p className="connect-note connect-caveat">
            개발자 모드는 현재 ChatGPT 웹의 Plus·Pro·Business·Enterprise·Education 계정에서
            제공되며, 조직 계정은 관리자 정책에 따라 제한될 수 있습니다.
          </p>
        </details>
        <details>
          <summary>기타 MCP 클라이언트</summary>
          <p className="connect-note">
            원격 MCP(streamable HTTP)를 지원하는 클라이언트라면 같은 주소로 등록할 수 있습니다.
            명세: <a href="/projects/public-data-lens/spec/tools/1.0" target="_blank" rel="noreferrer">Tool 스키마(JSON)</a>
          </p>
        </details>
      </div>

      {/* 입력 파라미터가 추가된 갱신 후 기존 연결은 옛 도구 목록을 계속 쓴다 —
          MCP 호스트가 연결 시점의 목록을 캐시하기 때문. 응답 필드 추가·데이터 갱신은 해당 없음. */}
      <p className="connect-note connect-caveat">
        <strong>새로 추가된 기능이 보이지 않으면</strong> 커넥터를 한 번 다시 연결해 주세요.
        AI 앱은 연결한 시점의 기능 목록을 기억하기 때문에, 그 뒤에 추가된 기능은
        재연결 후에 나타납니다. 데이터 갱신은 재연결 없이 바로 반영됩니다.
      </p>

      <h3>이렇게 물어보세요</h3>
      <ul className="about-list">
        {EXAMPLE_PROMPTS.map((p) => <li key={p}><em>“{p}”</em></li>)}
      </ul>

      <h3>제공 기능</h3>
      <p className="connect-note">
        데이터셋 검색 · 상세 조회 · 최대 5개 비교 · 월별 변경 확인 · 카탈로그 통계 ·
        컬럼 기준 검색 · 실제 파일 구조 확인 · <strong>데이터 활용 계획 초안(build_data_plan)</strong> ·
        서비스 안내 — 총 9개입니다. 하고 싶은 일을 한 문장으로 입력하면 후보 데이터의
        역할과 선정 근거, 연결에 사용할 것으로 예상되는 항목, 활용 전에 확인할 한계가
        포함된 계획 초안을 받을 수 있습니다. 각 결과에는 확인 근거와 적용한 규칙 버전이
        표시됩니다.
      </p>
    </section>
  )
}
