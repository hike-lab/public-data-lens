#!/bin/sh
# GATEWAY_REAL_IP_FROM(쉼표 구분 CIDR 목록)을 set_real_ip_from 지시문으로 전개한다.
# 단일 envsubst 슬롯은 CIDR 1개만 수용해 다중 대역 LB(ALB·CDN 등)에서 조용히 무력화되기 때문.
# 값이 없으면 기동을 중단한다 — 조용한 공유 버킷(전체 사용자 단일 rate limit)을 막는 fail-closed.
set -eu
: "${GATEWAY_REAL_IP_FROM:?GATEWAY_REAL_IP_FROM(신뢰할 LB 대역 CIDR, 쉼표 구분)을 지정해야 합니다 — 직접 노출이면 127.0.0.1}"
{
  echo "# 자동 생성(10-real-ip.sh) — GATEWAY_REAL_IP_FROM에서 전개. 잘못된 CIDR은 nginx -t가 기동 시 거부한다."
  for cidr in $(printf '%s' "$GATEWAY_REAL_IP_FROM" | tr ',' ' '); do
    printf 'set_real_ip_from %s;\n' "$cidr"
  done
  echo "real_ip_header X-Forwarded-For;"
  echo "real_ip_recursive on;"
} > /etc/nginx/conf.d/00-real-ip.conf
