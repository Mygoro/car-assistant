"""위치 서버만 단독 실행 — 봇 전체(STT/TTS) 없이 GPS 수신을 검증한다.

사용:
    uv run tools/location_only.py            # 포트 8765
    uv run tools/location_only.py 9000       # 다른 포트

띄운 뒤 다른 터미널에서:
    cloudflared tunnel --url http://localhost:8765
→ 나온 https 주소를 폰(브라우저 또는 GPSLogger)에 넣으면 좌표가 들어온다.
들어온 좌표는 콘솔에 주기적으로 출력된다.
"""
import asyncio
import io
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import location
from core.location_server import start_location_server


async def main(port: int) -> None:
    runner = await start_location_server(port)
    print(f"\n위치 서버 실행 중 — http://localhost:{port}")
    print("다른 터미널에서:  cloudflared tunnel --url http://localhost:" + str(port))
    print("폰에서 그 https 주소를 열거나 GPSLogger URL로 쏘면 아래에 좌표가 찍힙니다.")
    print("(Ctrl-C 종료)\n")
    last = None
    try:
        while True:
            await asyncio.sleep(3)
            cur = location.get_current()
            st = location.status()
            if cur != last:
                if cur:
                    print(f"📍 수신 (lon,lat)={cur}  정확도 ±{st['accuracy']}m  나이 {st['age_s']}s")
                last = cur
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    try:
        asyncio.run(main(port))
    except KeyboardInterrupt:
        print("\n종료")
