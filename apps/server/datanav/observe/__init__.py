"""데이터 구조 관측 계층 (설계: docs/데이터구조_관측_설계_v2_초안.md v2.2).

카탈로그 릴리스와 분리된 관측 스토어(data/observations/observations.db)를 관리한다.
모델: SourceAsset → StructureObservation(불변) → DataTable → FileColumn
상태: AssetCoverageState(가변) → RecordCoverageState(집계 뷰)
"""
