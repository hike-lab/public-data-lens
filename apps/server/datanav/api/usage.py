"""익명 사용 로그 공통 규칙(§10, 고지 v1.1) — REST(파일)와 MCP(stdout)가 같은 항목 규칙을 쓴다.

원칙: 원 IP 미저장(단방향 HMAC 일부만), UA 원문 미저장(클라이언트 종류로 정규화 —
지문화 방지), 옵트아웃(DNT/GPC/X-Datanav-No-Log) 시 전부 미기록, 질의 원문은 200자 캡.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets


# 익명 식별자용 HMAC 키 — 무염 해시는 IPv4 전수 역산이 가능하므로 비밀키 기반.
# 우선순위: 환경변수 > 데이터 볼륨에 1회 생성·영속 > 프로세스 임시 키(볼륨 읽기 전용 —
# 프로덕션 mcp 컨테이너가 이 경우다. 재시작 시 키가 바뀌어 기간 간 결합이 불가하지만,
# 사용량 지표 목적에는 충분하고 프라이버시로는 오히려 보수적이다).
def anon_hmac_key() -> bytes:
    env = os.environ.get("DATANAV_ANON_HMAC_KEY")
    if env:
        return env.encode()
    from .. import config
    p = config.DATA_DIR / "anon_hmac.key"
    try:
        key = p.read_bytes()
        if key:
            return key
    except OSError:
        pass
    key = secrets.token_bytes(32)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(key)
        p.chmod(0o600)
    except OSError:
        pass  # 기록 불가 환경(읽기 전용 볼륨) — 임시 키로 동작
    return key


def hash_ip(key: bytes, ip: str) -> str:
    """IP의 익명 HMAC 일부 — 원 IP는 저장하지 않는다."""
    return hmac.new(key, ip.encode(), hashlib.sha256).hexdigest()[:12]


# UA 원문은 지문화 소지가 있어 저장하지 않는다 — 알려진 클라이언트 종류로만 정규화.
_CLIENT_SIGNS = (
    ("claude-code", "claude-code"),
    ("claude", "claude"),          # Claude 웹·앱 커넥터(Anthropic 인프라 발신)
    ("openai", "openai"),          # ChatGPT 커넥터(OpenAI 인프라 발신)
    ("chatgpt", "openai"),
    ("python-httpx", "sdk"),
    ("node", "sdk"),
)


def normalize_client(user_agent: str | None) -> str:
    if not user_agent:
        return "unknown"
    ua = user_agent.lower()
    for sign, name in _CLIENT_SIGNS:
        if sign in ua:
            return name
    return "other"


def opted_out(headers) -> bool:
    """고지 §2 — DNT/GPC/X-Datanav-No-Log 신호가 있으면 해당 요청은 전부 미기록."""
    get = headers.get
    return get("dnt") == "1" or get("sec-gpc") == "1" or get("x-datanav-no-log") == "1"
