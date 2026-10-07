// 표시 언어(ko·en) 전환의 단일 지점 — 인터페이스 문안과 라벨 레지스트리만 바뀐다.
// 서버가 준 값(데이터셋 제목·기관명·설명·warnings[]·규칙 정의·지역명 등)은 어느 언어에서도
// 원문 그대로 표시한다(불변식 3·4). 영어 표면은 '한국어 카탈로그를 영어 인터페이스로 본다'는
// 뜻이며 데이터를 번역하지 않는다 — 이 사실은 EN 표면의 푸터·검색 힌트가 명시한다.
//
// 언어는 뷰 상태가 아니라 이용자 선호이므로 URL이 아니라 localStorage에 둔다.
// 초기값: 저장된 선호 → 브라우저 언어(ko*면 ko, 아니면 en) → ko.
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as LABELS_KO from './labels.js'
import * as LABELS_EN from './labels.en.js'
import { STRINGS_KO } from './strings.ko.jsx'
import { STRINGS_EN } from './strings.en.jsx'

export const LANGS = ['ko', 'en']
const STORAGE_KEY = 'datanav-lang'
const STRINGS = { ko: STRINGS_KO, en: STRINGS_EN }
const LABELS = { ko: LABELS_KO, en: LABELS_EN }
const TITLE = {
  ko: '공공데이터 렌즈 (Public Data Lens) — 근거 기반 공공데이터 탐색·판단',
  en: 'Public Data Lens — Evidence-based exploration of Korean public data',
}

export function detectLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (LANGS.includes(saved)) return saved
  } catch { /* 저장소 접근 불가 — 브라우저 언어로 */ }
  const nav = (typeof navigator !== 'undefined' && navigator.language) || 'ko'
  return nav.toLowerCase().startsWith('ko') ? 'ko' : 'en'
}

// {name} 자리 채움. 값이 함수면 vars를 넘겨 호출한다(어순이 다른 문장·JSX 조각용).
function resolve(table, key, vars) {
  const v = table[key]
  if (v === undefined) return undefined
  if (typeof v === 'function') return v(vars || {})
  if (typeof v === 'string' && vars) {
    return v.replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined && vars[k] !== null ? String(vars[k]) : m))
  }
  return v
}

export function makeT(lang) {
  const table = STRINGS[lang] || STRINGS_KO
  return (key, vars) => {
    const hit = resolve(table, key, vars)
    if (hit !== undefined) return hit
    // 누락 키는 한국어로 폴백한다 — 원시 키가 화면에 노출되지 않게(parity 테스트가 누락을 잡는다)
    const ko = resolve(STRINGS_KO, key, vars)
    return ko !== undefined ? ko : key
  }
}

const defaultValue = { lang: 'ko', setLang: () => {}, t: makeT('ko'), L: LABELS_KO }
const LangContext = createContext(defaultValue)

export function LangProvider({ children, initial }) {
  const [lang, setLangState] = useState(() => initial || detectLang())
  const setLang = useCallback((next) => {
    if (!LANGS.includes(next)) return
    setLangState(next)
    try { localStorage.setItem(STORAGE_KEY, next) } catch { /* 저장 불가 — 세션 한정 */ }
  }, [])
  useEffect(() => {
    // 문서 언어 속성은 스크린리더 발음·서체 폴백·api.js 오류 문안의 기준이 된다
    document.documentElement.lang = lang
    document.title = TITLE[lang]
  }, [lang])
  const value = useMemo(() => ({ lang, setLang, t: makeT(lang), L: LABELS[lang] }), [lang, setLang])
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}

// { lang, setLang, t, L } — L은 현재 언어의 라벨 레지스트리(labels.js와 동일한 export 이름)
export const useLang = () => useContext(LangContext)
