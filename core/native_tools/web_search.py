"""Brave Search native tool — web_search.

카카오 로컬 API가 주지 못하는 정보(영업시간, 가격, 메뉴, 가게 특징, 최신 뉴스 등)를
웹 검색으로 보완한다. BRAVE_API_KEY 환경변수 없으면 stub 응답 반환.

무료 티어: brave.com/search/api 에서 발급 (월 2,000건). 헤더 X-Subscription-Token 인증.
"""
import logging
import os
import re
from urllib.parse import urlparse

import httpx

log = logging.getLogger(__name__)

_BRAVE_BASE = "https://api.search.brave.com/res/v1/web/search"
_TAG_RE = re.compile(r"<[^>]+>")


def _clean(s: str) -> str:
    """Brave가 강조용으로 넣는 <strong> 등 HTML 태그 제거 + 공백 정리."""
    return _TAG_RE.sub("", s or "").strip()


async def web_search(args: dict) -> str:
    """웹 검색 (Brave Search).

    카카오에 없는 영업시간·가격·메뉴·가게 특징·최신 정보 조회에 사용.
    장소 자체(좌표/거리/길찾기)는 search_nearby_places·get_directions가 우선.

    args: query(검색어), count(결과 수, 기본 5, 최대 10)
    """
    key = os.environ.get("BRAVE_API_KEY")
    if not key:
        return "[stub] BRAVE_API_KEY 미설정 — 웹 검색 불가"

    query = args.get("query")
    if not query:
        return "[error] query가 필요합니다."
    count = min(int(args.get("count", 5)), 10)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                _BRAVE_BASE,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": key,
                },
                params={
                    "q": query,
                    "count": count,
                    "country": "kr",
                    "search_lang": "ko",
                    "ui_lang": "ko-KR",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("web", {}).get("results", [])
        if not results:
            return f"'{query}' 웹 검색 결과가 없습니다."

        lines = [f"'{query}' 웹 검색 결과:"]
        for r in results[:count]:
            title = _clean(r.get("title", ""))
            desc = _clean(r.get("description") or "")
            domain = urlparse(r.get("url", "")).netloc
            src = f" (출처: {domain})" if domain else ""
            lines.append(f"- {title}: {desc}{src}")
        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            log.error("Brave search auth error %s — 키 확인 필요", e.response.status_code)
            return "[웹 검색 오류: BRAVE_API_KEY 인증 실패]"
        if e.response.status_code == 429:
            return "[웹 검색 오류: 요청 한도 초과 (무료 티어 월 2,000건)]"
        log.error("Brave search error: %s", e)
        return f"[웹 검색 오류: {e}]"
    except Exception as e:
        log.error("Brave search error: %s", e)
        return f"[웹 검색 오류: {e}]"
