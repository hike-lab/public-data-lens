// English label registry — same export names as labels.js (the Korean canonical file).
// Contract codes stay untouched; only the display text changes. Key parity with labels.js
// is enforced by i18n.test.js, and closed enums are checked by scripts/check-labels.mjs.
// Terminology follows DESIGN.md §8: candidate / observed / confirmed / metadata /
// file observation / additional verification required. Never 'recommended', 'suitable',
// 'complete', 'best', 'AI-ready'.

// §2.9 update cycle (8)
export const UPDATE_CYCLE_LABEL = {
  DAILY: 'Daily', WEEKLY: 'Weekly', MONTHLY: 'Monthly', QUARTERLY: 'Quarterly',
  SEMIANNUAL: 'Semiannual', ANNUAL: 'Annual', IRREGULAR: 'Irregular', UNSPECIFIED: 'Not stated',
}

// open set — fallback allowed (excluded from the guard)
export const LICENSE_LABEL = {
  NO_RESTRICTION: 'No restriction',
  KOGL_BY: 'KOGL Type 1 (attribution)',
  KOGL_BY_NC: 'KOGL Type 2 (non-commercial)',
  KOGL_BY_ND: 'KOGL Type 3 (no derivatives)',
  KOGL_BY_NC_ND: 'KOGL Type 4 (non-commercial, no derivatives)',
  OTHER: 'Other (see source)',
  UNSPECIFIED: 'Not stated',
}

// §2.7 change status (6)
export const CHANGE_STATUS_LABEL = {
  ADDED: 'Added',
  MODIFIED: 'Modified',
  MISSING_FROM_SNAPSHOT: 'Not observed in this snapshot',
  REAPPEARED: 'Reappeared',
  POSSIBLE_IDENTITY_CHANGE: 'Same dataset? Verification needed',
  OFFICIALLY_WITHDRAWN: 'Officially withdrawn',
}

// §2.7 — absence from a snapshot is not withdrawal; goes in the body, not a tooltip
export const CHANGE_STATUS_NOTE = {
  MISSING_FROM_SNAPSHOT:
    'A record of the fact that this item was not observed in the current snapshot — not a confirmed withdrawal (withdrawal is shown only as "Officially withdrawn").',
  POSSIBLE_IDENTITY_CHANGE:
    'Title, agency or other fields changed substantially; whether this is the same dataset needs verification (could be a reorganisation or renaming).',
  REAPPEARED: 'Absent in the previous snapshot and observed again now.',
}

// §2.3 region evidence (5) — inference is neutral, not wrong
export const EVIDENCE_LABEL = {
  EXPLICIT_SPATIAL: 'Spatial coverage stated',
  INFERRED_FROM_TITLE: 'Inferred from title',
  INFERRED_FROM_PUBLISHER: 'Inferred from publisher',
  INFERRED_FROM_DESCRIPTION: 'Inferred from description',
  UNKNOWN: 'Region unknown',
}

// §2.4 structure collection status (10) — only COLLECTION_FAILED is a warning
export const COVERAGE_LABEL = {
  AVAILABLE: 'Column structure observed',
  PARTIAL: 'Column structure partially observed',
  NOT_COLLECTED: 'Not observed yet',
  QUEUED: 'Queued for collection',
  COLLECTING: 'Collecting',
  SOURCE_UNAVAILABLE: 'Source not reachable',
  UNSUPPORTED_FORMAT: 'Unsupported format',
  ACCESS_RESTRICTED: 'Access restricted',
  COLLECTION_FAILED: 'Structure collection failed',
  API_STRUCTURE_NOT_SUPPORTED_YET: 'API structure: planned for a later release',
}

// §2.5 example value status (6) × examplesPublic (policy flag)
export const EXAMPLE_STATUS_LABEL = {
  AVAILABLE: 'Examples shown',
  NO_NON_NULL_VALUES: 'No values',
  WITHHELD_BY_LICENSE: 'Withheld (license)',
  WITHHELD_BY_SAFETY: 'Withheld (safety)',
  NOT_COLLECTED: 'Not collected',
  COLLECTION_FAILED: 'Collection failed',
}

export const exampleStatusLabel = (status, examplesPublic) => {
  if (status === 'AVAILABLE' && !examplesPublic) return 'Not shown (policy)'
  return EXAMPLE_STATUS_LABEL[status] || status
}

// §2.6 freshness (3) — UNKNOWN is not bad
export const FRESHNESS_LABEL = {
  FRESH: { text: 'Recently updated', cls: 'fresh' },
  POSSIBLY_STALE: { text: 'Possibly stale', cls: 'stale' },
  UNKNOWN: { text: 'Freshness undetermined', cls: 'unknown' },
}

// §2.2 evidence level (2)
export const EVIDENCE_LEVEL_LABEL = {
  CATALOG_METADATA_ONLY: 'Catalog metadata',
  FILE_OBSERVATION: 'Actual file observed',
}

// §2.8 list type (3)
export const LIST_TYPE_LABEL = { FILE: 'File', API: 'API', STD: 'Standard' }

// family candidate review status (v1.8) — UNREVIEWED is 'not reviewed yet', not a failure
export const FAMILY_REVIEW_LABEL = {
  UNREVIEWED: 'Not reviewed yet',
  CONFIRMED_FAMILY: 'Confirmed family',
  LEGITIMATE_SPLIT: 'Legitimate split',
  NOT_A_FAMILY: 'Not a family',
}

// completeness checklist fields (open dictionary)
export const COMPLETENESS_FIELD_LABEL = {
  title: 'Title', theme: 'Category', org_name: 'Publisher', update_cycle: 'Update cycle',
  keywords: 'Keywords', description: 'Description', license: 'License', created_date: 'Registered',
  modified_date: 'Modified', list_url: 'Source URL', spatial: 'Spatial coverage', temporal: 'Temporal coverage',
  data_limits: 'Usage limits', format: 'Format', row_count: 'Row count', file_data_name: 'File name',
  api_type: 'API type', traffic: 'Traffic',
}

// the three decision-critical fields (completeness.keyFields)
export const KEY_FIELD_LABEL = { spatial: 'Spatial coverage', temporal: 'Period', dataLimits: 'Usage limits stated' }

// compare table fields (open dictionary)
export const COMPARE_FIELD_LABEL = {
  listType: 'List type', orgName: 'Publisher', theme: 'Category', formats: 'Formats',
  updateCycle: 'Update cycle', license: 'License', modifiedDate: 'Modified',
  createdDate: 'Registered', rowCount: 'Total rows', spatial: 'Spatial coverage', temporal: 'Temporal coverage',
  completenessScore: 'Completeness score', keywords: 'Keywords', fee: 'Fee', apiType: 'API type',
}

export const cycleLabel = (v) => UPDATE_CYCLE_LABEL[v] || v
export const licenseLabel = (v) => LICENSE_LABEL[v] || v

// ---- tables that used to live in components (mirrors of labels.js)

export const REGION_LABEL = {
  '': 'All regions', 'KR-11': 'Seoul', 'KR-26': 'Busan', 'KR-27': 'Daegu', 'KR-28': 'Incheon',
  'KR-29': 'Gwangju', 'KR-30': 'Daejeon', 'KR-31': 'Ulsan', 'KR-50': 'Sejong', 'KR-41': 'Gyeonggi',
  'KR-42': 'Gangwon', 'KR-43': 'Chungbuk', 'KR-44': 'Chungnam', 'KR-45': 'Jeonbuk', 'KR-46': 'Jeonnam',
  'KR-47': 'Gyeongbuk', 'KR-48': 'Gyeongnam', 'KR-49': 'Jeju',
}

export const MATCH_FIELD_LABEL = { title: 'title', keywords: 'keywords', description: 'description', orgName: 'publisher' }

export const INTERPRETED_FIELD_LABEL = { region: 'region', format: 'format', updateCycle: 'cycle', listType: 'type' }

export const ROLE_LABEL = {
  PRIMARY: 'Primary subject', DEMAND: 'Demand side', SUPPLY: 'Supply side',
  SPATIAL: 'Spatial join', TEMPORAL: 'Temporal join', REFERENCE: 'Reference / codes',
}
export const FIT_LABEL = {
  searchRelevance: 'Search relevance', structureEvidence: 'Structure evidence',
  freshness: 'Freshness', metadataCompleteness: 'Metadata filled',
}
export const NEED_STATUS_LABEL = { SATISFIED: 'Satisfied', UNSATISFIED: 'Unsatisfied', PARTIAL: 'Partially satisfied' }

export const COVERAGE_STATUS_NOTE = {
  AVAILABLE: 'Column names and basic structure were observed in the actual file — this does not vouch for the accuracy or quality of the values',
  NOT_COLLECTED: 'A matter of collection order, not of data quality.',
  QUEUED: 'Waiting for its turn in collection.',
  API_STRUCTURE_NOT_SUPPORTED_YET: 'Only file-type listings are observed for structure.',
}

export const EVIDENCE_LEVEL_NOTE = {
  CATALOG_METADATA_ONLY: 'The actual data content was not examined',
  FILE_OBSERVATION: 'Limited to the observed sample — not a guarantee of overall quality',
}

export const LENS_LABEL = {
  overview: 'Overview', structure: 'Structure', evidence: 'Evidence', uses: 'Plan draft', raw: 'Raw data',
}
export const RAW_VIEW_LABEL = { normalized: 'Normalized', source: 'Source', jsonld: 'JSON-LD' }
