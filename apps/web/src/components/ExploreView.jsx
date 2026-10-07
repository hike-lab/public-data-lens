// 둘러보기(2026-08-04 신설) — 홈은 검색 단독으로 비우고, "서비스가 데이터를 어떻게
// 읽는가"를 보여주는 쇼케이스 3블록(탐색 서사·데이터 해부·구조 관측 실물)을 여기로 옮겼다.
// 전부 기존 응답으로 채운다(§3 원칙 유지).
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useLang } from '../i18n.jsx'
import { ExplorationStoryBlock, AnatomyBlock } from './HomeBlocks.jsx'
import DatasetRow from './DatasetRow.jsx'

export default function ExploreView({ onOpen, planAvailable, onTryPurpose }) {
  const { t } = useLang()
  const [items, setItems] = useState([])
  useEffect(() => {
    api.search({ pageSize: 20 })
      .then((body) => setItems(body.data.items))
      .catch(() => setItems([]))
  }, [])

  const structured = items.filter((it) => it.structureAvailable).slice(0, 3)

  return (
    <section className="explore">
      <h2 className="explore-title">{t('explore.title')}</h2>
      <p className="result-meta">{t('explore.intro')}</p>

      {planAvailable && <ExplorationStoryBlock onTryPurpose={onTryPurpose} />}

      <AnatomyBlock items={items} onOpen={onOpen} />

      {structured.length > 0 && (
        <div className="home-block live-block">
          <h3>{t('explore.liveTitle')}</h3>
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
