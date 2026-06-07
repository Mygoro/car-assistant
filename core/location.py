"""세션 현재 위치 저장소 — 폰이 보내온 GPS 좌표를 보관한다.

폰 브라우저(location_server가 서빙하는 페이지)가 watchPosition으로 주기 전송하는
좌표를 set_current()로 저장하고, 위치 tool(search_nearby_places·get_directions)이
get_current()로 읽어 "근처/여기서"를 현재 좌표 기준으로 처리한다.

좌표는 (lon, lat) 순서로 반환한다 — 카카오 API의 x=경도, y=위도 규약에 맞춘다.
오래된 좌표(폰이 페이지를 닫아 갱신이 끊긴 경우)는 stale로 간주해 None을 돌려주고,
호출부는 지명 입력으로 폴백한다.
"""
import time

# 좌표가 이보다 오래되면(초) stale — 폰 전송이 끊긴 것으로 보고 폴백.
_MAX_AGE_S = 300

_state = {"lat": None, "lon": None, "accuracy": None, "ts": 0.0}


def set_current(lat: float, lon: float, accuracy: float | None = None) -> None:
    _state.update(lat=lat, lon=lon, accuracy=accuracy, ts=time.time())


def get_current(max_age_s: int = _MAX_AGE_S) -> tuple[float, float] | None:
    """신선한 현재 위치를 (lon, lat)로 반환. 없거나 stale이면 None."""
    if _state["lat"] is None:
        return None
    if time.time() - _state["ts"] > max_age_s:
        return None
    return (_state["lon"], _state["lat"])


def status() -> dict:
    """진단·로그용 현재 상태(나이 포함)."""
    has = _state["lat"] is not None
    age = time.time() - _state["ts"] if has else None
    return {
        "has_fix": has,
        "age_s": round(age, 1) if age is not None else None,
        "fresh": has and age is not None and age <= _MAX_AGE_S,
        "accuracy": _state["accuracy"],
    }
