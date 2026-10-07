import { useLang } from '../i18n.jsx'
import { rowButtonProps } from '../a11y.js'
import { RegionBadges } from './EvidenceRow.jsx'
import CoverageIndicator from './CoverageIndicator.jsx'

/* 완전성 표시(v1.1.0): 점수 막대 대신 "무엇이 기재됐는가".
   대부분(FILE의 89%)이 동일 점수라 %는 변별력이 없고, 실제 차이는
   판단 직결 3필드(공간·시간범위, 이용제한)의 기재 여부에서 나온다.
   기재된 것만 칩으로 보여주고(미기재가 기본이므로), 없으면 기재 수·표준 수준만 옅게 표기. */

function CompletenessBadges({ c }) {
  const { t, L } = useLang()
  const keys = Object.entries(c.keyFields || {}).filter(([, v]) => v)
  const title = t('row.completenessTitle', {
    filled: c.filledFields, total: c.totalFields, profile: c.profile, rule: c.rule,
    typical: c.typical, share: c.typicalShare, top: c.topPercent,
  })
  return (
    <span className="completeness" title={title}>
      {keys.map(([k]) => (
        <span key={k} className="key-field">{L.KEY_FIELD_LABEL[k]} ✓</span>
      ))}
      <span className="fill-count">
        {t('row.filled', { total: c.totalFields, filled: c.filledFields })}
        {c.typical ? t('row.typical') : t('row.topPercent', { p: c.topPercent })}
      </span>
    </span>
  )
}

export default function DatasetRow({ item, onOpen, compared, compareFull, onToggleCompare }) {
  const { t, L } = useLang()
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
          {item.rowCountListed != null && <span>{t('row.rows', { n: item.rowCountListed.toLocaleString() })}</span>}
        </div>
        {item.matchedColumns && (
          <p className="matched-columns">
            {t('row.matchedColumns')}{item.matchedColumns.map((m) => m.columns.join(', ')).join(' · ')}
          </p>
        )}
        {/* v1.6: '왜 이 결과인가' — 검색어가 나타난 필드(서버 사실, 프론트 재추정 아님) */}
        {item.matchedFields?.length > 0 && (
          <p className="matched-columns">
            {t('row.matchedFields')}{item.matchedFields.map((f) => L.MATCH_FIELD_LABEL[f] || f).join(', ')}
          </p>
        )}
        <div className="row-badges">
          {item.structureAvailable && <CoverageIndicator mode="chip" status="AVAILABLE" />}
          <CompletenessBadges c={item.completeness} />
          <RegionBadges regions={item.regions} short />
        </div>
      </div>
      <div className="row-actions">
        <label className="compare-check" title={t('row.compareTitle')}>
          <input
            type="checkbox"
            checked={compared}
            disabled={!compared && compareFull}
            onChange={() => onToggleCompare(item.recordId)}
          />
          {t('row.compare')}
        </label>
        {item.portalUrl && (
          <a href={item.portalUrl} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>
            {t('row.portal')}
          </a>
        )}
      </div>
    </li>
  )
}
