"""
Hyundai Developers OAuth 최초 인증 스크립트 (1회 실행).
실행: uv run tools/hyundai_auth.py
결과: core/native_tools/hyundai_token.json 생성
"""
import base64
import json
import os
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["HYUNDAI_CLIENT_ID"]
CLIENT_SECRET = os.environ["HYUNDAI_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8080/callback"
PORT = 8080
TOKEN_FILE = Path("core/native_tools/hyundai_token.json")

ACCOUNT_BASE = "https://prd.kr-ccapi.hyundai.com"
DATA_BASE = "https://dev.kr-ccapi.hyundai.com"


def _basic_auth() -> str:
    creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    return f"Basic {creds}"


def _wait_for_callback(wanted_param: str) -> str:
    """localhost:PORT에 임시 HTTP 서버를 띄우고, wanted_param을 받을 때까지 대기."""
    result: dict = {}

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            params = parse_qs(urlparse(self.path).query)
            if wanted_param in params:
                result[wanted_param] = params[wanted_param][0]
                body = "<html><body><h2>인증 완료</h2><p>창을 닫아도 됩니다.</p></body></html>".encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"unexpected callback")

        def log_message(self, *args):
            pass

    server = HTTPServer(("localhost", PORT), _Handler)
    server.timeout = 180
    while wanted_param not in result:
        server.handle_request()
    server.server_close()
    return result[wanted_param]


def step1_oauth() -> str:
    state = secrets.token_urlsafe(16)
    url = (
        f"{ACCOUNT_BASE}/api/v1/user/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&state={state}"
    )
    print("[1/4] 브라우저에서 현대차 로그인 창이 열립니다...")
    webbrowser.open(url)
    code = _wait_for_callback("code")
    print("      auth code 수신 완료")
    return code


def step2_token(code: str) -> dict:
    print("[2/4] access_token 발급 중...")
    with httpx.Client() as client:
        resp = client.post(
            f"{ACCOUNT_BASE}/api/v1/user/oauth2/token",
            headers={
                "Authorization": _basic_auth(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            content=urlencode({
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            }),
        )
    resp.raise_for_status()
    tokens = resp.json()
    print(f"      완료 (expires_in: {tokens.get('expires_in')}s)")
    return tokens


def step3_terms(access_token: str) -> None:
    print("[3/4] 개인정보 동의 상태 확인 중 (carlist 직접 시도)...")
    with httpx.Client() as client:
        resp = client.get(
            f"{DATA_BASE}/api/v1/car/profile/carlist",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if resp.status_code == 200:
        print("      동의 이미 완료 상태 — step3 건너뜀")
        return

    err = resp.json().get("errCode", "")
    if err == "5005":
        # 미동의 상태 — 브라우저 form 방식으로 동의 페이지 열기
        print("      동의 필요. 브라우저 폼 방식으로 진행...")
        _open_terms_in_browser(access_token)
    else:
        print(f"      carlist 응답 {resp.status_code} errCode={err} — 계속 진행")


def _open_terms_in_browser(access_token: str) -> None:
    """동의 페이지를 브라우저 form submit 방식으로 열기."""
    import tempfile
    state = secrets.token_urlsafe(16)
    html = f"""<!DOCTYPE html>
<html><body>
<p>잠시 후 동의 페이지로 이동합니다...</p>
<form id="f" method="POST" action="{DATA_BASE}/api/v1/car-service/terms/agreement">
  <input type="hidden" name="token" value="Bearer {access_token}">
  <input type="hidden" name="state" value="{state}">
</form>
<script>document.getElementById('f').submit();</script>
</body></html>"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_path = f.name

    print(f"      브라우저에서 동의를 완료해주세요...")
    webbrowser.open(f"file://{tmp_path}")
    _wait_for_callback("userId")
    print("      동의 완료")


def step4_carlist(access_token: str) -> str:
    print("[4/4] 차량 목록 조회 중...")
    with httpx.Client() as client:
        resp = client.get(
            f"{DATA_BASE}/api/v1/car/profile/carlist",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    resp.raise_for_status()
    cars = resp.json().get("cars", [])
    if not cars:
        raise RuntimeError("등록된 차량이 없습니다")
    car = cars[0]
    print(f"      {car['carSellname']} ({car['carType']}) — carId: {car['carId']}")
    return car["carId"]


def main():
    code = step1_oauth()
    tokens = step2_token(code)

    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")
    expires_at = int(time.time()) + int(tokens.get("expires_in", 7200))

    step3_terms(access_token)
    car_id = step4_carlist(access_token)

    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "car_id": car_id,
    }
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2), encoding="utf-8")
    print(f"\n완료! 저장: {TOKEN_FILE}")


if __name__ == "__main__":
    main()
