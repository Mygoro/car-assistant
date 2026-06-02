"""Hyundai Bluelink native tool — get_vehicle_status.

OAuth 미검증 상태. stub 응답 반환.
실연동 시 이 파일의 _fetch_bluelink()만 교체하면 됨.
"""
import logging
import os

log = logging.getLogger(__name__)

_STUB_DATA = {
    "fuel_pct": 42,
    "range_km": 320,
    "location": "연세대학교 인근",
    "odometer_km": 38200,
}


async def get_vehicle_status(args: dict) -> str:
    """차량 상태 조회 (연료, 주행거리, 위치).

    현재 stub 모드. HYUNDAI_CLIENT_ID 환경변수가 있으면 실연동 시도.
    """
    if os.environ.get("HYUNDAI_CLIENT_ID"):
        try:
            return await _fetch_bluelink()
        except Exception as e:
            log.error("Bluelink fetch failed, falling back to stub: %s", e)

    d = _STUB_DATA
    return (
        f"연료 잔여: {d['fuel_pct']}% (약 {d['range_km']}km 주행 가능)\n"
        f"누적 주행거리: {d['odometer_km']:,}km\n"
        f"마지막 주차 위치: {d['location']}\n"
        f"[stub 데이터 — Bluelink OAuth 미연결]"
    )


async def _fetch_bluelink() -> str:
    """TODO: Hyundai Developers Portal OAuth 2.0 실연동."""
    raise NotImplementedError("Bluelink OAuth 구현 전")
