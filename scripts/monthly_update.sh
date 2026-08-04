#!/usr/bin/env bash
# 월간 카탈로그 갱신 — 스냅샷 CSV 하나로 빌드→수용검사→원자적 배포→서비스 재기동까지 수행한다.
# 사용법: scripts/monthly_update.sh <목록개방현황.csv> <YYYY-MM>
#   공개 배포(MCP 전용) 스택: COMPOSE_FILE=docker-compose.prod.yml scripts/monthly_update.sh <CSV> <YYYY-MM>
# 전제: docker compose 스택 구성(.env 포함), CSV는 저장소 안(예: data/raw/incoming/)에 두면 컨테이너에서 접근 가능.
set -euo pipefail

cd "$(dirname "$0")/.."

CSV="${1:?사용법: monthly_update.sh <목록개방현황.csv> <YYYY-MM>}"
MONTH="${2:?사용법: monthly_update.sh <목록개방현황.csv> <YYYY-MM>}"

[[ "$MONTH" =~ ^[0-9]{4}-[0-9]{2}$ ]] || { echo "스냅샷 형식 오류: $MONTH (YYYY-MM)"; exit 1; }
[[ -f "$CSV" ]] || { echo "CSV 없음: $CSV"; exit 1; }

# CSV를 data/ 아래로 복사해 컨테이너 볼륨에서 보이게 한다
STAGE="data/raw/incoming"
mkdir -p "$STAGE"
BASENAME="$(basename "$CSV")"
[[ "$CSV" -ef "$STAGE/$BASENAME" ]] || cp "$CSV" "$STAGE/$BASENAME"

echo "== 빌드 (검증 실패 시 배포되지 않음 — 원자적 포인터 교체)"
docker compose run --rm api python scripts/build_catalog.py "/app/$STAGE/$BASENAME" "$MONTH"

echo "== 서비스 재기동 (api·mcp 모두 포인터 변경을 자동 감지하지만, 재기동으로 확정한다)"
docker compose restart api mcp

echo "== 12개월 초과 사용 로그 정리 (§10 보존 정책)"
find data/logs -name 'usage-*.jsonl' -mtime +365 -delete 2>/dev/null || true

echo "== 배포 확인 (컨테이너 내부에서 — prod 스택은 api 포트를 호스트에 노출하지 않는다)"
sleep 3
docker compose exec -T api python -c "
import json, urllib.request
d = json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/status', timeout=5))['data']
print('현재 스냅샷:', d['currentSnapshot'], '| 건수:', d['counts'])
"
echo "완료. 이전 릴리스 디렉터리는 보존됨(수동 정리)."
