"""Google Places API (New) native tool — get_place_details.

카카오가 못 주는 영업시간·평점·리뷰·가격대를 구조화해서 제공한다.
Text Search(New) 한 번 호출로 받으며, FieldMask로 요청 필드를 한정해 과금 SKU를 제어한다.

GOOGLE_MAPS_API_KEY 환경변수 없으면 stub 응답.
키 발급: Google Cloud 콘솔 → Maps Platform → Places API (New) 활성화 → API 키.
무료 한도(월): Contact(영업시간/전화) 5,000건, Atmosphere(평점/리뷰/가격) 1,000건.
"""
import logging
import os

import httpx

log = logging.getLogger(__name__)

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# 요청 필드. reviews/rating/priceLevel은 Atmosphere SKU(월 1,000 무료),
# openingHours/phone은 Contact SKU(월 5,000 무료). 가장 비싼 필드 기준 과금.
_FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.priceLevel",
    "places.currentOpeningHours.openNow",
    "places.regularOpeningHours.weekdayDescriptions",
    "places.nationalPhoneNumber",
    "places.reviews",
])

_PRICE = {
    "PRICE_LEVEL_FREE": "무료",
    "PRICE_LEVEL_INEXPENSIVE": "저렴",
    "PRICE_LEVEL_MODERATE": "보통",
    "PRICE_LEVEL_EXPENSIVE": "비싼 편",
    "PRICE_LEVEL_VERY_EXPENSIVE": "매우 비쌈",
}


async def get_place_details(args: dict) -> str:
    """장소의 영업시간·평점·리뷰·가격대 조회 (Google Places).

    "지금 영업해?", "평점 어때?", "비싼 곳이야?", "리뷰 어때?" 류에 사용.
    단순 위치/거리/길찾기는 search_nearby_places·get_directions가 우선.

    args: query(장소명, 지역 포함 권장. 예: '잠실 핫이즈타코', '강남 스타벅스 강남대로점')
    """
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        return "[stub] GOOGLE_MAPS_API_KEY 미설정 — 장소 상세 조회 불가"

    query = args.get("query")
    if not query:
        return "[error] query가 필요합니다."

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                _SEARCH_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": key,
                    "X-Goog-FieldMask": _FIELD_MASK,
                },
                json={
                    "textQuery": query,
                    "languageCode": "ko",
                    "regionCode": "KR",
                    "maxResultCount": 1,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        places = data.get("places", [])
        if not places:
            return f"'{query}' 장소를 찾을 수 없습니다."

        p = places[0]
        name = p.get("displayName", {}).get("text", query)
        lines = [f"{name}"]

        addr = p.get("formattedAddress")
        if addr:
            lines.append(f"주소: {addr}")

        rating = p.get("rating")
        if rating is not None:
            cnt = p.get("userRatingCount", 0)
            lines.append(f"평점: {rating} (리뷰 {cnt:,}개)")

        price = _PRICE.get(p.get("priceLevel", ""))
        if price:
            lines.append(f"가격대: {price}")

        open_now = p.get("currentOpeningHours", {}).get("openNow")
        if open_now is not None:
            lines.append(f"현재: {'영업 중' if open_now else '영업 종료'}")

        phone = p.get("nationalPhoneNumber")
        if phone:
            lines.append(f"전화: {phone}")

        hours = p.get("regularOpeningHours", {}).get("weekdayDescriptions", [])
        if hours:
            lines.append("영업시간:")
            lines.extend(f"  {h}" for h in hours)

        reviews = p.get("reviews", [])
        if reviews:
            lines.append("리뷰:")
            for rv in reviews[:2]:
                txt = (rv.get("text", {}).get("text") or "").strip().replace("\n", " ")
                if len(txt) > 150:
                    txt = txt[:150] + "…"
                rscore = rv.get("rating", "")
                lines.append(f"  ({rscore}점) {txt}")

        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            log.error("Places auth error %s — 키/Places API 활성화 확인", e.response.status_code)
            return "[장소 상세 오류: GOOGLE_MAPS_API_KEY 인증 실패 또는 Places API 미활성화]"
        if e.response.status_code == 429:
            return "[장소 상세 오류: 요청 한도 초과]"
        log.error("Places error: %s", e)
        return f"[장소 상세 오류: {e}]"
    except Exception as e:
        log.error("Places error: %s", e)
        return f"[장소 상세 오류: {e}]"
