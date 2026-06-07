"""KakaoMap native tools — search_nearby_places, reverse_geocode, get_directions.

KAKAO_REST_API_KEY 환경변수 없으면 stub 응답 반환.
길찾기(get_directions)는 같은 REST 키를 쓰며, 콘솔에서 "카카오내비" 사용 설정이 켜져 있어야 한다.
"""
import logging
import os
import re

import httpx

log = logging.getLogger(__name__)

_KAKAO_BASE = "https://dapi.kakao.com"
_NAVI_BASE = "https://apis-navi.kakaomobility.com"


def _headers() -> dict:
    """카카오 Local API(dapi.kakao.com)용 — developers.kakao.com REST 키."""
    key = os.environ.get("KAKAO_REST_API_KEY", "")
    return {"Authorization": f"KakaoAK {key}"}


def _navi_key() -> str:
    """카카오내비 길찾기(apis-navi.kakaomobility.com)용 — developers.kakaomobility.com에서
    별도 발급한 REST 키. 미설정 시 KAKAO_REST_API_KEY로 폴백(같은 키를 쓰는 환경 대비)."""
    return os.environ.get("KAKAOMOBILITY_REST_API_KEY") or os.environ.get("KAKAO_REST_API_KEY", "")


def _navi_headers() -> dict:
    return {"Authorization": f"KakaoAK {_navi_key()}"}


async def search_nearby_places(args: dict) -> str:
    """장소 검색 (주유소, 충전소, 음식점 등).

    좌표(lon, lat)는 선택. 없으면 지역명을 query에 포함해 검색
    (예: "강남역 주유소"). 카카오 keyword API가 질의어에서 지역을 직접 파싱한다.

    args: query, lon(선택), lat(선택), radius_m (default 5000, 좌표 있을 때만 적용)
    """
    if not os.environ.get("KAKAO_REST_API_KEY"):
        return "[stub] 카카오 REST API 키 미설정 — 장소 검색 불가"

    query = args.get("query", "주유소")
    lon = args.get("lon")
    lat = args.get("lat")
    radius = args.get("radius_m", 5000)

    params = {"query": query, "size": 5}
    has_coord = lon is not None and lat is not None
    if has_coord:
        params.update({"x": lon, "y": lat, "radius": radius, "sort": "distance"})

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

        header = f"'{query}' 검색 결과 (반경 {radius}m):" if has_coord else f"'{query}' 검색 결과:"
        lines = [header]
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


async def _geocode(client: httpx.AsyncClient, name: str) -> tuple[float, float, str] | None:
    """지명/주소 → (lon, lat, 정제된 place_name). keyword 검색 첫 결과 사용. 실패 시 None."""
    resp = await client.get(
        f"{_KAKAO_BASE}/v2/local/search/keyword.json",
        headers=_headers(),
        params={"query": name, "size": 1},
    )
    resp.raise_for_status()
    docs = resp.json().get("documents", [])
    if not docs:
        return None
    d = docs[0]
    return float(d["x"]), float(d["y"]), d.get("place_name", name)


def _normalize_departure_time(value: str) -> str | None:
    """ISO/자연어 datetime → 카카오 future API용 YYYYMMDDHHMM. 자릿수 부족 시 None.

    예: "2026-06-07T09:00:00" → "202606070900", "202606070900" → 그대로.
    """
    digits = re.sub(r"\D", "", value or "")
    return digits[:12] if len(digits) >= 12 else None


async def get_directions(args: dict) -> str:
    """출발지→목적지 자동차 경로의 소요시간/거리/통행료.

    출발지/목적지를 지명 문자열로 받아 내부에서 좌표로 변환 후 경로 탐색.
    GPS 불필요 — 두 지명 사이 경로를 서버가 계산한다.

    departure_time(선택)을 주면 그 미래 시각 기준 교통량으로 예측
    (/v1/future/directions). 없으면 현재 시각 기준(/v1/directions).

    args: origin(지명), destination(지명),
          priority(RECOMMEND/TIME/DISTANCE, 기본 RECOMMEND),
          departure_time(선택, ISO datetime 또는 YYYYMMDDHHMM, 현재 이후만 유효)

    인증: 지오코딩은 KAKAO_REST_API_KEY(Local API), 경로 탐색은 KAKAOMOBILITY_REST_API_KEY
    (developers.kakaomobility.com 별도 발급). 후자 미설정 시 전자로 폴백.
    """
    if not os.environ.get("KAKAO_REST_API_KEY"):
        return "[stub] 카카오 REST API 키 미설정 — 길찾기 불가"
    if not _navi_key():
        return "[stub] 카카오모빌리티 키 미설정 — 길찾기 불가"

    origin_name = args.get("origin")
    dest_name = args.get("destination")
    priority = args.get("priority", "RECOMMEND")
    departure_raw = args.get("departure_time")
    if not origin_name or not dest_name:
        return "[error] origin, destination이 필요합니다."

    departure_time = None
    if departure_raw:
        departure_time = _normalize_departure_time(departure_raw)
        if departure_time is None:
            return f"[error] departure_time 형식 오류: '{departure_raw}' (YYYYMMDDHHMM 필요)"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            origin = await _geocode(client, origin_name)
            if origin is None:
                return f"출발지 '{origin_name}'을(를) 찾을 수 없습니다."
            dest = await _geocode(client, dest_name)
            if dest is None:
                return f"목적지 '{dest_name}'을(를) 찾을 수 없습니다."

            o_lon, o_lat, o_label = origin
            d_lon, d_lat, d_label = dest

            params = {
                "origin": f"{o_lon},{o_lat}",
                "destination": f"{d_lon},{d_lat}",
                "priority": priority,
                "summary": "true",
            }
            if departure_time:
                params["departure_time"] = departure_time
                endpoint = f"{_NAVI_BASE}/v1/future/directions"
            else:
                endpoint = f"{_NAVI_BASE}/v1/directions"

            resp = await client.get(endpoint, headers=_navi_headers(), params=params)
            resp.raise_for_status()
            data = resp.json()

        routes = data.get("routes", [])
        if not routes:
            return "경로를 찾을 수 없습니다."
        route = routes[0]
        if route.get("result_code") != 0:
            return f"길찾기 실패: {route.get('result_msg', '알 수 없는 오류')}"

        summary = route["summary"]
        minutes = round(summary["duration"] / 60)
        km = round(summary["distance"] / 1000, 1)
        toll = summary.get("fare", {}).get("toll", 0)
        when = ""
        if departure_time:
            t = departure_time
            when = f"{t[4:6]}월 {t[6:8]}일 {t[8:10]}:{t[10:12]} 출발 기준 "
        return f"{when}{o_label} → {d_label}: 약 {minutes}분, {km}km, 통행료 {toll:,}원"

    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            log.error("Kakao directions auth error %s — 콘솔에서 카카오내비 활성화 필요", e.response.status_code)
            return "[Kakao directions error: 카카오내비 사용 설정이 필요합니다]"
        log.error("Kakao directions error: %s", e)
        return f"[Kakao directions error: {e}]"
    except Exception as e:
        log.error("Kakao directions error: %s", e)
        return f"[Kakao directions error: {e}]"
