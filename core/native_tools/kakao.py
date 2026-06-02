"""KakaoMap native tools — search_nearby_places, reverse_geocode.

KAKAO_REST_API_KEY 환경변수 없으면 stub 응답 반환.
"""
import logging
import os

import httpx

log = logging.getLogger(__name__)

_KAKAO_BASE = "https://dapi.kakao.com"


def _headers() -> dict:
    key = os.environ.get("KAKAO_REST_API_KEY", "")
    return {"Authorization": f"KakaoAK {key}"}


async def search_nearby_places(args: dict) -> str:
    """주변 장소 검색 (주유소, 충전소, 음식점 등).

    args: query, lon, lat, radius_m (default 5000)
    """
    if not os.environ.get("KAKAO_REST_API_KEY"):
        return "[stub] 카카오 REST API 키 미설정 — 주변 주유소 검색 불가"

    query = args.get("query", "주유소")
    lon = args.get("lon")
    lat = args.get("lat")
    radius = args.get("radius_m", 5000)

    if lon is None or lat is None:
        return "[error] 위치 정보(lon, lat)가 필요합니다."

    params = {
        "query": query,
        "x": lon,
        "y": lat,
        "radius": radius,
        "size": 5,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{_KAKAO_BASE}/v2/local/search/keyword.json",
                headers=_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        places = data.get("documents", [])
        if not places:
            return f"'{query}' 검색 결과가 없습니다."

        lines = [f"'{query}' 검색 결과 (반경 {radius}m):"]
        for p in places:
            name = p.get("place_name", "")
            addr = p.get("road_address_name") or p.get("address_name", "")
            dist = p.get("distance", "")
            dist_str = f" ({dist}m)" if dist else ""
            lines.append(f"- {name}: {addr}{dist_str}")
        return "\n".join(lines)

    except Exception as e:
        log.error("Kakao search error: %s", e)
        return f"[Kakao search error: {e}]"


async def reverse_geocode(args: dict) -> str:
    """GPS 좌표 → 한국어 주소.

    args: lon, lat
    """
    if not os.environ.get("KAKAO_REST_API_KEY"):
        return "[stub] 카카오 REST API 키 미설정 — 역지오코딩 불가"

    lon = args.get("lon")
    lat = args.get("lat")
    if lon is None or lat is None:
        return "[error] lon, lat이 필요합니다."

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{_KAKAO_BASE}/v2/local/geo/coord2address.json",
                headers=_headers(),
                params={"x": lon, "y": lat},
            )
            resp.raise_for_status()
            data = resp.json()

        docs = data.get("documents", [])
        if not docs:
            return f"좌표 ({lat}, {lon})에 해당하는 주소를 찾을 수 없습니다."

        addr = docs[0]
        road = addr.get("road_address", {})
        jibun = addr.get("address", {})
        road_name = road.get("address_name", "") if road else ""
        jibun_name = jibun.get("address_name", "") if jibun else ""
        return road_name or jibun_name or f"좌표 ({lat}, {lon})"

    except Exception as e:
        log.error("Kakao reverse geocode error: %s", e)
        return f"[Kakao geocode error: {e}]"
