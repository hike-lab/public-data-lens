import { useState } from 'react'
import { useLang } from '../i18n.jsx'

// 정본 URI(§7 영구 불변)를 안내한다 — 화면 origin을 쓰면 dev·프리뷰에서
// 동작하지 않는 로컬 주소가 복사된다(P0). 정본은 배포 후 변경 불가이므로 상수가 맞다.
const MCP_URL = 'https://service.datahub.kr/projects/public-data-lens/mcp'

export default function ConnectView() {
  const { t } = useLang()
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
        <h2>{t('connect.heroTitle')}</h2>
        <p>{t('connect.heroBody')}</p>
      </div>

      <div className="mcp-url">
        <code>{MCP_URL}</code>
        <button onClick={copy}>{copied ? t('connect.copied') : t('connect.copy')}</button>
      </div>

      {/* capability demonstration — 설치 안내보다 먼저, 무엇이 달라지는지(§3 #7).
          결과를 날조하지 않는다: 단계는 실제 Tool 파이프라인, 응답 항목은 계약 필드다 */}
      <h3>{t('connect.capTitle')}</h3>
      <div className="cap-demo">
        <div className="cap-col">
          <h4>{t('connect.capAsk')}</h4>
          <p className="cap-quote">{t('connect.capQuote')}</p>
        </div>
        <div className="cap-col">
          <h4>{t('connect.capSteps')}</h4>
          <ol className="cap-steps">
            <li>{t('connect.step1')} <code>build_data_plan</code></li>
            <li>{t('connect.step2')} <code>search_by_columns</code></li>
            <li>{t('connect.step3')} <code>compare_datasets</code></li>
            <li>{t('connect.step4')} <code>get_dataset_structure</code></li>
          </ol>
        </div>
        <div className="cap-col">
          <h4>{t('connect.capOut')}</h4>
          <ul className="cap-out">
            <li>{t('connect.out1')}</li>
            <li>{t('connect.out2')}</li>
            <li>{t('connect.out3')}</li>
            <li>{t('connect.out4')}</li>
          </ul>
        </div>
      </div>

      <h3>{t('connect.howTitle')}</h3>
      {/* 카드 3열은 정보량 불균형으로 폐기(P2) — 같은 구조의 아코디언으로 */}
      <div className="connect-acc">
        <details open>
          <summary>{t('connect.claudeWeb')}</summary>
          <ol className="mcp-steps">
            {t('connect.claudeSteps').map((step, i) => <li key={i}>{step}</li>)}
          </ol>
          <p className="connect-note connect-caveat">{t('connect.claudeCaveat')}</p>
          <p className="connect-note">{t('connect.claudePermission')}</p>
        </details>
        <details>
          <summary>{t('connect.claudeCode')}</summary>
          <pre className="connect-code">{`claude mcp add \\
  --transport http \\
  public-data-lens \\
  ${MCP_URL}`}</pre>
          <p className="connect-note">{t('connect.claudeCodeCheck')}</p>
        </details>
        <details>
          <summary>{t('connect.chatgpt')}</summary>
          <ol className="mcp-steps">
            <li>{t('connect.chatgptStep1')}</li>
            <li>{t('connect.chatgptStep2')}</li>
            <li>
              {t('connect.chatgptStep3')}
              <table className="connect-table">
                <tbody>
                  {t('connect.chatgptTable', { mcpUrl: MCP_URL }).map(([k, v], i) => (
                    <tr key={i}><th>{k}</th><td>{v}</td></tr>
                  ))}
                </tbody>
              </table>
            </li>
            <li>{t('connect.chatgptStep4')}</li>
            <li>{t('connect.chatgptStep5')}</li>
            <li>{t('connect.chatgptStep6')}</li>
          </ol>
          <p className="connect-note">{t('connect.chatgptCheck')}</p>
          <p className="connect-note connect-caveat">{t('connect.chatgptCaveat')}</p>
        </details>
        <details>
          <summary>{t('connect.other')}</summary>
          <p className="connect-note">{t('connect.otherBody')}</p>
        </details>
      </div>

      {/* 입력 파라미터가 추가된 갱신 후 기존 연결은 옛 도구 목록을 계속 쓴다 —
          MCP 호스트가 연결 시점의 목록을 캐시하기 때문. 응답 필드 추가·데이터 갱신은 해당 없음. */}
      <p className="connect-note connect-caveat">{t('connect.reconnect')}</p>

      <h3>{t('connect.askTitle')}</h3>
      <ul className="about-list">
        {t('connect.examplePrompts').map((p) => <li key={p}><em>“{p}”</em></li>)}
      </ul>

      <h3>{t('connect.featuresTitle')}</h3>
      <p className="connect-note">{t('connect.featuresBody')}</p>
    </section>
  )
}
