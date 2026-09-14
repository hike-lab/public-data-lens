// 표시 언어 계층의 불변 검증 — 두 언어의 키 집합이 같고(누락 키는 원시 키·한국어 폴백으로
// 화면에 노출된다), 라벨 레지스트리의 export·키가 동일하며, t()의 자리 채움·함수·폴백이 동작한다.
import { describe, it, expect } from 'vitest'
import { STRINGS_KO } from './strings.ko.jsx'
import { STRINGS_EN } from './strings.en.jsx'
import * as KO from './labels.js'
import * as EN from './labels.en.js'
import { makeT } from './i18n.jsx'

describe('strings parity', () => {
  it('영어 사전은 한국어 사전과 같은 키 집합을 가진다', () => {
    const ko = Object.keys(STRINGS_KO).sort()
    const en = Object.keys(STRINGS_EN).sort()
    expect(en).toEqual(ko)
  })

  it('같은 키는 같은 종류의 값을 가진다(문자열·함수·배열·객체)', () => {
    const kind = (v) => (Array.isArray(v) ? 'array' : typeof v)
    for (const k of Object.keys(STRINGS_KO)) {
      expect(kind(STRINGS_EN[k]), k).toBe(kind(STRINGS_KO[k]))
    }
  })

  it('예시 질의(q)는 두 언어에서 같다 — 한국어 카탈로그를 조회하므로', () => {
    for (const k of ['search.examples', 'search.columnExamples', 'search.purposeExamples']) {
      expect(STRINGS_EN[k].map((x) => x.q)).toEqual(STRINGS_KO[k].map((x) => x.q))
    }
    expect(STRINGS_EN['home.storyPurpose'].q).toBe(STRINGS_KO['home.storyPurpose'].q)
  })
})

describe('labels parity', () => {
  it('labels.en.js는 labels.js와 같은 export를 가진다', () => {
    expect(Object.keys(EN).sort()).toEqual(Object.keys(KO).sort())
  })

  it('각 라벨 테이블의 키(계약 코드)는 두 언어에서 같다', () => {
    for (const name of Object.keys(KO)) {
      if (typeof KO[name] !== 'object') continue
      expect(Object.keys(EN[name]).sort(), name).toEqual(Object.keys(KO[name]).sort())
    }
  })

  it('영어 라벨은 DESIGN §8 회피 어휘를 쓰지 않는다', () => {
    const banned = /\b(recommended|guaranteed|ai-ready|suitable|optimal|best)\b/i
    const walk = (v) => {
      if (typeof v === 'string') expect(v, v).not.toMatch(banned)
      else if (v && typeof v === 'object') Object.values(v).forEach(walk)
    }
    walk(EN)
    Object.values(STRINGS_EN).forEach((v) => { if (typeof v === 'string') walk(v) })
  })
})

describe('makeT', () => {
  it('자리 채움·함수 값·누락 폴백', () => {
    const t = makeT('en')
    expect(t('search.total', { n: '1,234' })).toBe('1,234 results')
    expect(t('cov.population', { searched: '10', total: null })).toBe('Searched within 10 records with observed structure')
    expect(makeT('ko')('cov.population', { searched: '10', total: '20' })).toBe('구조가 관측된 10건 (전체 파일 목록 20건) 중 검색')
    expect(t('no.such.key')).toBe('no.such.key')
  })
})
