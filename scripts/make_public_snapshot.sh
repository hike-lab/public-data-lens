#!/bin/sh
# 공개 릴리스 스냅샷 생성 — 컨시어지(별도 서비스) 구현을 제외한 트리를 만든다.
#
# 사용:  scripts/make_public_snapshot.sh <출력디렉터리>
# 결과:  <출력디렉터리>에 HEAD 기준 트리(컨시어지 제외)가 생성된다. 연구실 공개 repo에는
#        이 트리를 새 커밋(릴리스 스냅샷)으로 push한다.
#
# 전제(코드 계약): 서버는 concierge*.py 부재 시 라우트를 자동 미등록(rest.py의 조건부 import),
# 웹은 ConciergeView.jsx 부재 시 import.meta.glob이 빈 객체를 반환해 표면이 사라진다(App.jsx).
# 따라서 이 스크립트는 파일 삭제 + 설정 파일의 몇 줄 정리만 수행하며 코드 패치를 하지 않는다.
#
# 검증(스냅샷 디렉터리에서):
#   cd apps/server && python -m pytest        # 컨시어지 테스트 제외 수집, 0 오류
#   python -c "from datanav.api.rest import app"
#   cd apps/web && npm ci && npm run build     # ConciergeView 청크가 없어야 한다
set -eu

OUT="${1:?사용법: scripts/make_public_snapshot.sh <출력디렉터리>}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  echo "오류: 출력 디렉터리가 비어 있지 않습니다: $OUT" >&2
  exit 1
fi
mkdir -p "$OUT"

git archive HEAD | tar -x -C "$OUT"

# ---- 컨시어지 전용 파일 제거(코드 수정 불필요 — 위 계약 참조)
EXCLUDE="
apps/server/datanav/api/concierge.py
apps/server/datanav/api/concierge_routes.py
apps/server/tests/test_concierge.py
apps/server/scripts/bench_concierge.py
apps/server/scripts/concierge_smoke.py
apps/server/scripts/score_bench.py
apps/server/golden/bench_v0_report.json
apps/web/src/components/ConciergeView.jsx
apps/web/src/components/ConciergeDashboard.jsx
apps/web/nginx.concierge.conf
docker-compose.concierge.yml
docs/공공데이터_내비게이터_구현정리_v1.0.pptx
docs/구현현황_설계대조_v1.0.md
docs/데이터구조_관측_설계_v2_초안.md
docs/어휘_매핑_확장_제안_v1.md
docs/차기_기능_백로그_v1.0.md
AGENTS.md
"
# 개발 에이전트 워크플로 잔재 — AGENTS.md(에이전트 규칙 문서)와 .claude/(Claude Code 설정)는
# 개발 저장소 전용이므로 공개 릴리스에서 제외한다.
rm -rf "$OUT/.claude"

# 공개판 README 교체 — 개발용 README 대신 핵심만 담은 공개판을 쓴다.
mv "$OUT/README.public.md" "$OUT/README.md"

# 매핑표의 내부 문서 링크를 일반 텍스트로 (어휘 제안 문서는 공개판에서 제외됨)
sed -i.bak 's|\[어휘 매핑 확장 제안 v1.1\](어휘_매핑_확장_제안_v1.md)|어휘 매핑 확장 제안 v1.1(내부 검토 문서)|' "$OUT/docs/매핑표_v1.0.md" && rm -f "$OUT/docs/매핑표_v1.0.md.bak"
for f in $EXCLUDE; do
  if [ -e "$OUT/$f" ]; then
    rm "$OUT/$f"
  else
    echo "경고: 제외 대상이 없습니다(목록 갱신 필요): $f" >&2
  fi
done

# ---- 설정 파일에서 컨시어지 잔재 정리(전부 no-op 항목 — 남아도 동작엔 무해)
# .env.example: ANTHROPIC_API_KEY 줄 + 컨시어지 블록(## 생성형 컨시어지 ~ 파일 끝) 제거
sed -i.bak '/^ANTHROPIC_API_KEY=/d; /^## 생성형 컨시어지/,$d' "$OUT/.env.example" && rm -f "$OUT/.env.example.bak"
# docker-compose.yml(dev): ANTHROPIC_API_KEY 전달 줄 제거
sed -i.bak '/ANTHROPIC_API_KEY/d' "$OUT/docker-compose.yml" && rm -f "$OUT/docker-compose.yml.bak"
# docker-compose.prod.yml: DATANAV_CONCIERGE_ENABLED(모듈 부재로 no-op) 줄과 그 주석 제거
sed -i.bak '/생성형 컨시어지는 이 배포에 포함되지 않는다 — 별도 서비스(docker-compose.concierge.yml)/d; /DATANAV_CONCIERGE_ENABLED/d' "$OUT/docker-compose.prod.yml" && rm -f "$OUT/docker-compose.prod.yml.bak"
# .gitignore: 컨시어지 사용량 파일 ignore(죽은 규칙) 제거
sed -i.bak '/concierge_usage.json/d' "$OUT/.gitignore" && rm -f "$OUT/.gitignore.bak"
# pyproject: anthropic 의존성 제거(유일 소비자가 concierge.py) + lock의 직접 핀 제거
sed -i.bak '/"anthropic>=/d' "$OUT/apps/server/pyproject.toml" && rm -f "$OUT/apps/server/pyproject.toml.bak"
sed -i.bak '/^anthropic==/d' "$OUT/apps/server/requirements.lock" && rm -f "$OUT/apps/server/requirements.lock.bak"
# 서버 Dockerfile 머리 주석
sed -i.bak 's/(2층 REST + 컨시어지)/(2층 REST)/' "$OUT/apps/server/Dockerfile" && rm -f "$OUT/apps/server/Dockerfile.bak"

echo "완료: $OUT"
echo "잔여 컨시어지 언급(관계 설명·게이트웨이 404 차단 등 정책상 유지분):"
grep -ril -E "concierge|컨시어지" "$OUT" --include="*.py" --include="*.jsx" --include="*.yml" --include="*.conf" --include="*.template" --include="*.md" | sed "s|^$OUT/||" || true
