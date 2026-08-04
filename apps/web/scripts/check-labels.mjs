// 라벨 커버리지 빌드 가드(가이드 §2.1) — 계약 스펙의 닫힌 enum과 labels.js를 대조해
// 누락이 있으면 빌드를 실패시킨다. 계약에 enum이 추가될 때 원시 코드가 사용자에게
// 노출되는 것을 막는다. license는 열린 집합이라 제외(폴백 라벨 허용).
import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const specDir = path.resolve(here, '../../server/datanav/spec')
const specFile = readdirSync(specDir).filter((f) => /^tool-schemas-v[\d.]+\.json$/.test(f)).sort().at(-1)
const spec = JSON.parse(readFileSync(path.join(specDir, specFile), 'utf-8'))

// 스펙 전체에서 enum 배열 수집
const enums = []
;(function walk(o) {
  if (Array.isArray(o)) return o.forEach(walk)
  if (o && typeof o === 'object') {
    if (Array.isArray(o.enum)) enums.push(o.enum)
    Object.values(o).forEach(walk)
  }
})(spec)

// 시그니처 멤버로 축을 식별(속성명 'status'가 축마다 겹치므로 내용으로 판별)
const findEnum = (signature) => {
  const hit = enums.find((e) => e.includes(signature))
  if (!hit) throw new Error(`계약에서 enum을 찾지 못함(시그니처: ${signature}) — ${specFile}`)
  return hit.filter((v) => v !== null)
}

// labels.js에서 테이블 키 추출(정규식 — 단순 식별자 키만 쓰는 파일 규약)
const labelsSrc = readFileSync(path.resolve(here, '../src/labels.js'), 'utf-8')
const tableKeys = (name) => {
  // 여러 줄 테이블(\n} 종결) 우선, 한 줄 테이블({ ... }) 폴백
  const m = labelsSrc.match(new RegExp(`export const ${name} = \\{([\\s\\S]*?)\\n\\}`))
    || labelsSrc.match(new RegExp(`export const ${name} = \\{(.*?)\\}`))
  if (!m) throw new Error(`labels.js에 ${name} 없음`)
  // 키는 위치 무관 추출 — 중첩 값 객체의 내부 키(text·cls)가 섞여도 누락 검사(⊇)에는 무해
  return new Set([...m[1].matchAll(/([A-Za-z_][A-Za-z0-9_]*)\s*:/g)].map((x) => x[1]))
}

const checks = [
  ['COVERAGE_LABEL', findEnum('API_STRUCTURE_NOT_SUPPORTED_YET')],
  ['EVIDENCE_LABEL', findEnum('EXPLICIT_SPATIAL')],
  ['EXAMPLE_STATUS_LABEL', findEnum('WITHHELD_BY_SAFETY')],
  ['FRESHNESS_LABEL', findEnum('POSSIBLY_STALE')],
  ['CHANGE_STATUS_LABEL', findEnum('MISSING_FROM_SNAPSHOT')],
  ['LIST_TYPE_LABEL', findEnum('STD')],
  // updateCycle은 계약 출력 스키마에 enum이 없다(입력 설명문에만 존재) —
  // 가이드 §2.9의 8종을 기준으로 대조한다. 계약에 enum이 추가되면 위 방식으로 전환.
  ['UPDATE_CYCLE_LABEL', ['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMIANNUAL', 'ANNUAL', 'IRREGULAR', 'UNSPECIFIED']],
]

let failed = false
for (const [table, contract] of checks) {
  const have = tableKeys(table)
  const missing = contract.filter((v) => !have.has(v))
  if (missing.length) {
    failed = true
    console.error(`✗ ${table}: 계약 enum ${contract.length}종 중 누락 ${missing.length} — ${missing.join(', ')}`)
  } else {
    console.log(`✓ ${table}: ${contract.length}/${contract.length} (${specFile})`)
  }
}
if (failed) {
  console.error('\n라벨 커버리지 가드 실패 — labels.js를 완결하라(가이드 §2.1~§2.10).')
  process.exit(1)
}
