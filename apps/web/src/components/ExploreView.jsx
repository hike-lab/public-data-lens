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
        제목 검색이 아니라 구조·근거·한계의 탐색입니다. 아래는 전부 현재 스냅샷의 실데이터입니다.
      </p>

      {planAvailable && <ExplorationStoryBlock onTryPurpose={onTryPurpose} />}

      <AnatomyBlock items={items} onOpen={onOpen} />

      {structured.length > 0 && (
        <div className="home-block live-block">
          <h3>지금 바로 구조까지 볼 수 있는 데이터 — 최신 수정분 중 3건</h3>
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
