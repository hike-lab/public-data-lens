import { KEY_FIELD_LABEL } from '../labels.js'

const MATCH_FIELD_LABEL = { title: '제목', keywords: '키워드', description: '설명', orgName: '기관' }
import { rowButtonProps } from '../a11y.js'
import { RegionBadges } from './EvidenceRow.jsx'
import CoverageIndicator from './CoverageIndicator.jsx'

/* 완전성 표시(v1.1.0): 점수 막대 대신 "무엇이 기재됐는가".
   대부분(FILE의 89%)이 동일 점수라 %는 변별력이 없고, 실제 차이는
   판단 직결 3필드(공간·시간범위, 이용제한)의 기재 여부에서 나온다.
   기재된 것만 칩으로 보여주고(미기재가 기본이므로), 없으면 기재 수·표준 수준만 옅게 표기. */

function CompletenessBadges({ c }) {
  const keys = Object.entries(c.keyFields || {}).filter(([, v]) => v)
  const title = `메타데이터 ${c.filledFields}/${c.totalFields} 항목 기재 (${c.profile} 프로파일, ${c.rule})`
      + (c.typical ? ` — 동일 유형의 ${c.typicalShare}%가 같은 수준` : ` — 상위 ${c.topPercent}%`)
  return (
    <span className="completeness" title={title}>
      {keys.map(([k]) => (
        <span key={k} className="key-field">{KEY_FIELD_LABEL[k]} ✓</span>
      ))}
      <span className="fill-count">
        메타데이터 {c.filledFields}/{c.totalFields} 항목
        {c.typical ? ' · 표준 수준' : ` · 상위 ${c.topPercent}%`}
      </span>
    </span>
  )
}

export default function DatasetRow({ item, onOpen, compared, compareFull, onToggleCompare }) {
  return (
    <li className="result-row">
      <div className="row-main" {...rowButtonProps(() => onOpen(item.recordId))}>
        <div className="row-title">
          <span className={`type type-${item.listType}`}>{item.listType}</span>
          <strong>{item.title}</strong>
          {item.modifiedDate && <span className="row-date">{item.modifiedDate}</span>}
        </div>
        <div className="row-sub">
          <span>{item.orgName}</span>
          {item.theme?.top && <span>{item.theme.top}{item.theme.sub ? ` › ${item.theme.sub}` : ''}</span>}
          {item.formats?.length > 0 && <span>{item.formats.join(' · ')}</span>}
          {item.rowCountListed != null && <span>행 {item.rowCountListed.toLocaleString()}</span>}
        </div>
        {item.matchedColumns && (
          <p className="matched-columns">
            일치 컬럼: {item.matchedColumns.map((m) => m.columns.join(', ')).join(' · ')}
          </p>
        )}
        {/* v1.6: '왜 이 결과인가' — 검색어가 나타난 필드(서버 사실, 프론트 재추정 아님) */}
        {item.matchedFields?.length > 0 && (
          <p className="matched-columns">
            검색어 일치: {item.matchedFields.map((f) => MATCH_FIELD_LABEL[f] || f).join(', ')}
          </p>
        )}
        <div className="row-badges">
          {item.structureAvailable && <CoverageIndicator mode="chip" status="AVAILABLE" />}
          <CompletenessBadges c={item.completeness} />
          <RegionBadges regions={item.regions} short />
        </div>
      </div>
      <div className="row-actions">
        <label className="compare-check" title="비교에 추가 (최대 5개)">
          <input
            type="checkbox"
            checked={compared}
            disabled={!compared && compareFull}
            onChange={() => onToggleCompare(item.recordId)}
          />
          비교
        </label>
        {item.portalUrl && (
          <a href={item.portalUrl} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>
            포털 원문 ↗
          </a>
        )}
      </div>
    </li>
  )
}
