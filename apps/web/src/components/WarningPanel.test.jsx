// 서버 경고 무치환 렌더 + 상시 고지 필터(단일 정책 지점) 검증.
import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import WarningPanel from './WarningPanel.jsx'

describe('WarningPanel', () => {
  it('서버 문안을 치환 없이 그대로 표시한다', () => {
    const w = '이 검색은 구조가 관측된 59,395건 안에서만 수행되었습니다 — INFERRED_FROM_TITLE 포함.'
    const { container } = render(<WarningPanel warnings={[w]} />)
    expect(container.querySelector('.notice').textContent).toBe(w)
  })

  it('상시 고지(면책·생성형)는 반복하지 않는다', () => {
    const { container } = render(
      <WarningPanel warnings={[
        '본 결과는 공공데이터포털 목록 메타데이터 기반이며 …',
        '생성형 응답은 참고용입니다 …',
        '비교 기준 이전 스냅샷이 없습니다.',
      ]} />,
    )
    const notices = container.querySelectorAll('.notice')
    expect(notices.length).toBe(1)
    expect(notices[0].textContent).toContain('이전 스냅샷')
  })

  it('표시할 것이 없으면 아무것도 그리지 않는다', () => {
    const { container } = render(<WarningPanel warnings={['본 결과는 …']} />)
    expect(container.innerHTML).toBe('')
    expect(render(<WarningPanel />).container.innerHTML).toBe('')
  })

  it('error는 경고보다 먼저 표시한다', () => {
    const { container } = render(<WarningPanel warnings={['개별 경고']} error="요청 실패" />)
    expect(container.querySelector('.error').textContent).toBe('요청 실패')
    expect(container.querySelector('.notice').textContent).toBe('개별 경고')
  })
})
