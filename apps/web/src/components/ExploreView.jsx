// 둘러보기(2026-08-04 신설) — 홈은 검색 단독으로 비우고, "서비스가 데이터를 어떻게
// 읽는가"를 보여주는 쇼케이스 3블록(탐색 서사·데이터 해부·구조 관측 실물)을 여기로 옮겼다.
// 전부 기존 응답으로 채운다(§3 원칙 유지).
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { ExplorationStoryBlock, AnatomyBlock } from './HomeBlocks.jsx'
import DatasetRow from './DatasetRow.jsx'

export default function ExploreView({ onOpen, planAvailable, onTryPurpose }) {
  const [items, setItems] = useState([])
  useEffect(() => {
    api.search({ pageSize: 20 })
      .then((body) => setItems(body.data.items))
      .catch(() => setItems([]))
  }, [])

  const structured = items.filter((it) => it.structureAvailable).slice(0, 3)

  return (
    <section className="explore">
      <h2 className="explore-title">둘러보기 — 이 서비스는 데이터를 이렇게 읽습니다</h2>
      <p className="result-meta">
        데이터 제목만 검색하지 않습니다. 데이터의 구조와 선정 근거, 활용할 때 확인해야 할
        한계까지 함께 살펴봅니다. 아래 예시는 현재 서비스에 반영된 공공데이터포털의 실제
        목록을 바탕으로 합니다.
      </p>

      {planAvailable && <ExplorationStoryBlock onTryPurpose={onTryPurpose} />}

      <AnatomyBlock items={items} onOpen={onOpen} />

      {structured.length > 0 && (
        <div className="home-block live-block">
          <h3>구조를 바로 확인할 수 있는 데이터 — 최근 수정된 데이터 중 3건</h3>
          <ul className="results">
            {structured.map((item) => (
              <DatasetRow
                key={item.recordId}
                item={item}
                onOpen={onOpen}
                compared={false}
                compareFull
                onToggleCompare={() => {}}
              />
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
