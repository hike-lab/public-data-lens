// §2.4 절대 규칙 검증: COLLECTION_FAILED 하나만 경고 표시, 나머지 9종은 전부 중립.
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import CoverageIndicator, { CoveragePopulation } from './CoverageIndicator.jsx'
import { COVERAGE_LABEL } from '../labels.js'

const ALL_STATUSES = Object.keys(COVERAGE_LABEL) // 10종 — labels.js가 빌드 가드로 계약과 동기화됨

describe('CoverageIndicator (note 모드, 분모 없음)', () => {
  it.each(ALL_STATUSES)('%s: 라벨을 원시 코드 대신 표시한다', (status) => {
    const { container } = render(<CoverageIndicator status={status} />)
    expect(container.textContent).toContain(COVERAGE_LABEL[status])
  })

  it('COLLECTION_FAILED만 경고 클래스를 가진다 — 나머지는 전부 중립', () => {
    for (const status of ALL_STATUSES) {
      const { container, unmount } = render(<CoverageIndicator status={status} />)
      const note = container.querySelector('.coverage-note')
      expect(note.className).toContain(`s-${status}`)
      if (status !== 'COLLECTION_FAILED') {
        expect(note.className).not.toContain('COLLECTION_FAILED')
      }
      unmount()
    }
  })

  it('NOT_COLLECTED에는 수집 순번 부연이 붙는다(품질 오해 방지)', () => {
    render(<CoverageIndicator status="NOT_COLLECTED" />)
    expect(screen.getByText(/수집 순번/)).toBeTruthy()
  })

  it('알 수 없는 상태는 코드 그대로 노출한다(라벨 날조 금지)', () => {
    const { container } = render(<CoverageIndicator status="FUTURE_STATUS" />)
    expect(container.textContent).toContain('FUTURE_STATUS')
  })
})

describe('CoverageIndicator (분모 있음)', () => {
  it('파일 분자/분모를 함께 표시한다', () => {
    const { container } = render(
      <CoverageIndicator status="AVAILABLE" available={3} total={5} examplesPublic />,
    )
    expect(container.textContent).toContain('파일 3/5개 관측')
    expect(container.querySelector('.ex-policy')).toBeNull()
  })

  it('examplesPublic=false면 정책 비공개를 명시한다', () => {
    const { container } = render(
      <CoverageIndicator status="AVAILABLE" available={3} total={5} examplesPublic={false} />,
    )
    expect(container.querySelector('.ex-policy').textContent).toContain('예시값 비공개')
  })
})

describe('CoverageIndicator (chip 모드)', () => {
  it('AVAILABLE 칩은 경고 클래스 없이 라벨만 표시한다', () => {
    const { container } = render(<CoverageIndicator mode="chip" status="AVAILABLE" />)
    const chip = container.querySelector('.structure-chip')
    expect(chip.textContent).toBe(COVERAGE_LABEL.AVAILABLE)
    expect(chip.className).not.toContain('COLLECTION_FAILED')
  })

  it('COLLECTION_FAILED 칩만 경고 클래스를 가진다', () => {
    const { container } = render(<CoverageIndicator mode="chip" status="COLLECTION_FAILED" />)
    expect(container.querySelector('.structure-chip').className).toContain('s-COLLECTION_FAILED')
  })
})

describe('CoveragePopulation (검색 모집단)', () => {
  it('분모가 있으면 함께 표시한다(§4.2 — 분모 없이 표시 금지)', () => {
    const { container } = render(<CoveragePopulation searched={59395} total={83695} />)
    expect(container.textContent).toContain('59,395건')
    expect(container.textContent).toContain('83,695건')
  })

  it('searched가 없으면 아무것도 그리지 않는다', () => {
    const { container } = render(<CoveragePopulation />)
    expect(container.textContent).toBe('')
  })
})
