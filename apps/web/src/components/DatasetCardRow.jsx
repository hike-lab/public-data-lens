const EVIDENCE_LABEL = {
  EXPLICIT_SPATIAL: '공간범위 명시',
  INFERRED_FROM_TITLE: '제목 추론',
  INFERRED_FROM_PUBLISHER: '기관명 추론',
  INFERRED_FROM_DESCRIPTION: '설명 추론',
}

/* 완전성 표시(v1.1.0): 점수 막대 대신 "무엇이 기재됐는가".
   대부분(FILE의 89%)이 동일 점수라 %는 변별력이 없고, 실제 차이는
   판단 직결 3필드(공간·시간범위, 이용제한)의 기재 여부에서 나온다.
   기재된 것만 칩으로 보여주고(미기재가 기본이므로), 없으면 기재 수·표준 수준만 옅게 표기. */
const KEY_FIELD_LABEL = { spatial: '공간범위', temporal: '기간', dataLimits: '이용제한 명시' }

function CompletenessBadges({ c }) {
  const keys = Object.entries(c.keyFields || {}).filter(([, v]) => v)
  const title = `목록 메타데이터 기재 ${c.filledFields}/${c.totalFields} (${c.profile} 프로파일, ${c.rule})`
      + (c.typical ? ` — 동일 유형의 ${c.typicalShare}%가 같은 수준` : ` — 상위 ${c.topPercent}%`)
  return (
    <span className="completeness" title={title}>
      {keys.map(([k]) => (
        <span key={k} className="key-field">{KEY_FIELD_LABEL[k]} ✓</span>
      ))}
      <span className="fill-count">
        기재 {c.filledFields}/{c.totalFields}
        {c.typical ? ' · 표준 수준' : c.topPercent <= 10 ? ` · 상위 ${c.topPercent}%` : ''}
      </span>
    </span>
  )
}

export default function DatasetCardRow({ item, onOpen, compared, compareFull, onToggleCompare }) {
  return (
    <li className="card-row">
      <div className="card-main" onClick={() => onOpen(item.recordId)}>
        <div className="card-title-line">
          <span className={`type type-${item.listType}`}>{item.listType}</span>
          <strong>{item.title}</strong>
        </div>
        <div className="card-sub">
          <span>{item.orgName}</span>
          {item.theme?.top && <span>{item.theme.top}{item.theme.sub ? ` › ${item.theme.sub}` : ''}</span>}
          {item.formats?.length > 0 && <span>{item.formats.join(' · ')}</span>}
          {item.modifiedDate && <span>수정 {item.modifiedDate}</span>}
        </div>
        {item.matchedColumns && (
          <p className="matched-columns">
            일치 컬럼: {item.matchedColumns.map((m) => m.columns.join(', ')).join(' · ')}
          </p>
        )}
        <div className="card-badges">
          {item.structureAvailable && (
            <span className="key-field structure-chip" title="실제 파일에서 원본 컬럼·유형이 관측됨 — 프로필의 '데이터 구조' 탭에서 확인">
              구조 확인됨
            </span>
          )}
          <CompletenessBadges c={item.completeness} />
          {item.regions?.map((r) => (
            <span
              key={r.code}
              className={`region ${r.evidence === 'EXPLICIT_SPATIAL' ? 'explicit' : 'inferred'}`}
              title={`${EVIDENCE_LABEL[r.evidence] || r.evidence} · 신뢰도 ${r.confidence}`}
            >
              {r.name.replace(/(특별자치|특별|광역)?(시|도)$/, '')}
              {r.evidence !== 'EXPLICIT_SPATIAL' && '?'}
            </span>
          ))}
        </div>
      </div>
      <div className="card-actions">
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
