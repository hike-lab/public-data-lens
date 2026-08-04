// 근거 표기가 evidenceLevel 값에서 도출되는지(하드코딩 아님) 검증.
import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import EvidenceRow, { RegionBadges } from './EvidenceRow.jsx'

describe('EvidenceRow', () => {
  it('CATALOG_METADATA_ONLY: 라벨·코드·미확인 부연을 함께 표시한다', () => {
    const { container } = render(<EvidenceRow level="CATALOG_METADATA_ONLY" />)
    const t = container.textContent
    expect(t).toContain('메타데이터 기준')
    expect(t).toContain('CATALOG_METADATA_ONLY')
    expect(t).toContain('실제 데이터 내용은 확인되지 않았습니다')
  })

  it('FILE_OBSERVATION: 관측 라벨과 표본 한정 부연을 표시한다', () => {
    const { container } = render(<EvidenceRow level="FILE_OBSERVATION" />)
    expect(container.textContent).toContain('실제 파일 구조 관측')
    expect(container.textContent).toContain('표본 한정')
  })

  it('관측 메타(일자·출처·스캔 범위)를 표시한다', () => {
    const { container } = render(
      <EvidenceRow
        className="obs-meta"
        observation={{ observedAt: '2026-07-15T09:00:00Z', provenance: 'PROFILE_CSV', scanScope: 'FULL' }}
      />,
    )
    expect(container.querySelector('.obs-meta').textContent)
      .toBe('관측 2026-07-15 · PROFILE_CSV · 스캔 FULL')
  })

  it('표시할 근거가 없으면 아무것도 그리지 않는다', () => {
    const { container } = render(<EvidenceRow />)
    expect(container.innerHTML).toBe('')
  })
})

describe('RegionBadges', () => {
  const regions = [
    { code: '11', name: '서울특별시', evidence: 'EXPLICIT_SPATIAL', confidence: 0.99 },
    { code: '26', name: '부산광역시', evidence: 'INFERRED_FROM_TITLE', confidence: 0.8 },
  ]

  it('추론 배지에는 텍스트로 "추론"을 병기한다(색만으로 구분 금지)', () => {
    const { container } = render(<RegionBadges regions={regions} />)
    const badges = container.querySelectorAll('.region')
    expect(badges[0].className).toContain('explicit')
    expect(badges[0].querySelector('.inf-mark')).toBeNull()
    expect(badges[1].className).toContain('inferred')
    expect(badges[1].querySelector('.inf-mark').textContent).toBe('추론')
  })

  it('short 옵션은 표시 축약일 뿐 기본은 서버 값 그대로다', () => {
    const full = render(<RegionBadges regions={regions} />)
    expect(full.container.textContent).toContain('서울특별시')
    const short = render(<RegionBadges regions={regions} short />)
    expect(short.container.querySelectorAll('.region')[0].textContent).toContain('서울')
    expect(short.container.textContent).not.toContain('서울특별시')
  })
})
