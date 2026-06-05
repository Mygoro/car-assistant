"""Hyundai Bluelink native tool — get_vehicle_status.

공식 Hyundai Developers API 사용 (dev.kr-ccapi.hyundai.com).
필요 파일: core/native_tools/hyundai_token.json (tools/hyundai_auth.py 실행 후 생성)
제공 데이터: 주행 가능 거리(DTE), 누적 주행거리(Odometer)
미제공: 연료 잔량 %, GPS 위치 (한국 공식 API 미지원)
"""
import asyncio
import base64
import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

log = logging.getLogger(__name__)

_TOKEN_FILE = Path("core/native_tools/hyundai_token.json")
_ACCOUNT_BASE = "https://prd.kr-ccapi.hyundai.com"
_DATA_BASE = "https://dev.kr-ccapi.hyundai.com"
_UNIT_MAP = {0: "feet", 1: "km", 2: "m", 3: "miles"}


def _basic_auth() -> str:
    cid = os.environ["HYUNDAI_CLIENT_ID"]
    csec = os.environ["HYUNDAI_CLIENT_SECRET"]
    return "Basic " + base64.b64encode(f"{cid}:{csec}".encode()).decode()


def _load_token() -> dict:
    if not _TOKEN_FILE.exists():
        raise FileNotFoundError(
            "hyundai_token.json 없음. tools/hyundai_auth.py 먼저 실행하세요."
        )
    return json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))


def _save_token(data: dict) -> None:
    _TOKEN_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _ensure_token() -> dict:
    data = _load_token()
    if time.time() < data["expires_at"] - 300:
        return data

    log.info("Hyundai access_token 만료, 갱신 중...")
    with httpx.Client() as client:
        resp = client.post(
            f"{_ACCOUNT_BASE}/api/v1/user/oauth2/token",
            headers={
                "Authorization": _basic_auth(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            content=urlencode({
                "grant_type": "refresh_token",
                "refresh_token": data["refresh_token"],
                "redirect_uri": "http://localhost:8080/callback",
            }),
        )
    resp.raise_for_status()
    new_tokens = resp.json()
    data["access_token"] = new_tokens["access_token"]
    data["expires_at"] = int(time.time()) + int(new_tokens.get("expires_in", 7200))
    if new_tokens.get("refresh_token"):
        data["refresh_token"] = new_tokens["refresh_token"]
    _save_token(data)
    return data


def _fetch() -> str:
    token_data = _ensure_token()
    access_token = token_data["access_token"]
    car_id = token_data["car_id"]
    headers = {"Authorization": f"Bearer {access_token}"}
    lines = []

    with httpx.Client(timeout=10) as client:
        dte = client.get(
            f"{_DATA_BASE}/api/v1/car/status/{car_id}/dte", headers=headers
        )
        if dte.status_code == 200:
            d = dte.json()
            unit = _UNIT_MAP.get(d.get("unit", 1), "km")
            lines.append(f"주행 가능 거리: {d['value']}{unit}")
        else:
            lines.append(f"주행 가능 거리: 조회 실패 ({dte.status_code})")

        odo = client.get(
            f"{_DATA_BASE}/api/v1/car/status/{car_id}/odometer", headers=headers
        )
        if odo.status_code == 200:
            odometers = odo.json().get("odometers", [])
            if odometers:
                latest = odometers[-1]
                unit = _UNIT_MAP.get(latest.get("unit", 1), "km")
                lines.append(f"누적 주행거리: {int(latest['value']):,}{unit}")
        else:
            lines.append(f"누적 주행거리: 조회 실패 ({odo.status_code})")

    return "\n".join(lines)


async def get_vehicle_status(args: dict) -> str:
    """차량 상태 조회 (주행 가능 거리, 누적 주행거리)."""
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    except FileNotFoundError as e:
        return f"[Vehicle error: {e}]"
    except Exception as e:
        log.error("Vehicle status error: %s", e)
        return f"[Vehicle error: {e}]"
