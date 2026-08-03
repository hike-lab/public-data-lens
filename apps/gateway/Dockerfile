# 공개 게이트웨이(A 스택) — 리버스 프록시(랜딩은 코어 웹이 담당).
# GATEWAY_REAL_IP_FROM(쉼표 구분 다중 CIDR)은 엔트리포인트 스크립트가 set_real_ip_from으로 전개한다.
# 기본값을 두지 않는다 — 미지정 시 기동 실패(fail-closed)가 의도된 동작.
FROM nginx:alpine
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY 10-real-ip.sh /docker-entrypoint.d/10-real-ip.sh
RUN chmod +x /docker-entrypoint.d/10-real-ip.sh
EXPOSE 80
