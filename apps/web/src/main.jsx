import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
// 서체 셀프호스팅: Pretendard 가변 동적 서브셋(한글+라틴 — 라틴은 Inter 파생),
// IBM Plex Mono는 기계가 정한 문자열(recordId·ruleId·enum·원본 컬럼명) 전용
import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/600.css'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
