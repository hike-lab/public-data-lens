// 관측 현황 — 계약 의미 검증: 미산출 ≠ 0건, 축적 단계 ≠ 고장, 프로파일 분리 유지,
// UNREVIEWED는 '검토 전'(문제 프레임 금지). 수치는 서버 응답 그대로 표기한다.
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

const envelope = (data) => ({ data, meta: {}, warnings: [], notices: [] })

vi.mock('../api.js', () => ({
  api: {
    stats: vi.fn((axis) => {
      if (axis === 'listType') {
        return Promise.resolve(envelope({ axis, buckets: [{ key: 'FILE', count: 83876 }, { key: 'API', count: 11278 }] }))
      }
      if (axis === 'completeness') {
        return Promise.resolve(envelope({
          axis,
          profiles: [
            { profile: 'FILE', rule: 'catalog-completeness-file-v1.0', average: 0.8134, histogram: [] },
            { profile: 'API', rule: 'catalog-completeness-api-v1.0', average: null, histogram: [] },
          ],
        }))
      }
      if (axis === 'family') {
        return Promise.resolve(envelope({ axis, available: false, note: '도입 전 빌드' }))
      }
      return Promise.resolve(envelope({ axis, buckets: [{ key: '교육', count: 9000 }] }))
    }),
    statsBreakdown: vi.fn(() => Promise.resolve(envelope({
      axis: 'org', breakdown: 'listType',
      buckets: [{ key: '서울특별시', count: 3294, breakdown: { FILE: 3215, API: 79 } }],
    }))),
    changes: vi.fn(() => Promise.resolve(envelope({ baseSnapshot: null, currentSnapshot: '2026-06', items: [], summary: {} }))),
  },
}))

import ObservatoryView from './ObservatoryView.jsx'

const status = envelope({
  currentSnapshot: '2026-06',
  counts: { datasets: 96056 },
  structureCoverage: { recordsAvailable: 59395, fileRecordsTotal: 83876 },
})

describe('ObservatoryView', () => {
  it('계열 미산출을 0건이 아니라 상태로 표기한다', async () => {
    render(<ObservatoryView status={status} />)
    await waitFor(() => expect(screen.getByText(/0건이라는 뜻은 아닙니다/)).toBeTruthy())
  })

  it('첫 스냅샷 축적 단계를 고장이 아니라 사실로 안내한다', async () => {
    render(<ObservatoryView status={status} />)
    await waitFor(() => expect(screen.getByText(/스냅샷을 축적하는 단계/)).toBeTruthy())
  })

  it('완전성은 프로파일별로만 표기하고 합산 수치를 만들지 않는다', async () => {
    const { container } = render(<ObservatoryView status={status} />)
    await waitFor(() => expect(container.querySelectorAll('.obs-profiles li').length).toBeGreaterThan(0))
    expect(container.textContent).toContain('유형 간 수치를 합치거나 직접 비교하지 않습니다')
    // average null은 0%가 아니라 '산출 대상 없음'
    expect(container.textContent).toContain('산출 대상 없음')
    expect(container.textContent).not.toContain('0.0%')
  })

  it('구조 미관측을 수집 상태로 설명한다(품질 문제 프레임 금지)', async () => {
    render(<ObservatoryView status={status} />)
    await waitFor(() => expect(screen.getByText(/품질이 낮다는 뜻은 아닙니다/)).toBeTruthy())
  })

  it('기관 버킷에 서버 교차 집계를 그대로 부기한다', async () => {
    const { container } = render(<ObservatoryView status={status} />)
    await waitFor(() => expect(container.querySelector('.obs-extra')).toBeTruthy())
    expect(container.querySelector('.obs-extra').textContent).toContain('파일 3,215')
  })
})
