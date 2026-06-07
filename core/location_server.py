"""폰 GPS 수신용 경량 HTTP 서버 (봇과 같은 이벤트 루프에서 실행).

- GET  /      → 폰용 위치 공유 페이지(navigator.geolocation.watchPosition)
- POST /loc   → {lat, lon, accuracy}를 받아 core.location에 저장

geolocation은 보안 컨텍스트(HTTPS 또는 localhost)에서만 동작하므로, 폰에서 쓸 땐
`cloudflared tunnel --url http://localhost:<port>`로 만든 https URL을 폰 브라우저에서 연다.
"""
import logging

from aiohttp import web

from . import location

log = logging.getLogger(__name__)

_PAGE = """<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>OTTO 위치 공유</title>
<style>
  body{font-family:-apple-system,system-ui,sans-serif;margin:0;padding:2rem;
       text-align:center;background:#0f1115;color:#e8eaed}
  h1{font-size:1.3rem;margin:.5rem 0 1.5rem}
  #status{font-size:1.1rem;margin:1rem 0;min-height:1.5em}
  #coord{font-size:.95rem;color:#9aa0a6;font-variant-numeric:tabular-nums}
  .ok{color:#34d399}.err{color:#f87171}
  .hint{margin-top:2rem;font-size:.85rem;color:#6b7280;line-height:1.5}
</style></head>
<body>
  <h1>🚗 OTTO 위치 공유</h1>
  <div id="status">위치 권한을 요청합니다…</div>
  <div id="coord"></div>
  <div class="hint">이 화면을 켜둔 채로 두세요.<br>화면이 꺼지거나 닫히면 위치 전송이 멈춥니다.</div>
<script>
  var s=document.getElementById('status'), c=document.getElementById('coord');
  if(!navigator.geolocation){ s.textContent='이 브라우저는 위치를 지원하지 않습니다.'; s.className='err'; }
  else {
    navigator.geolocation.watchPosition(async function(p){
      var lat=p.coords.latitude, lon=p.coords.longitude, acc=p.coords.accuracy;
      c.textContent = lat.toFixed(5)+', '+lon.toFixed(5)+'  (±'+Math.round(acc)+'m)';
      try{
        await fetch('/loc',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({lat:lat,lon:lon,accuracy:acc})});
        s.textContent='✅ 위치 전송 중'; s.className='ok';
      }catch(e){ s.textContent='전송 오류: '+e; s.className='err'; }
    }, function(e){ s.textContent='위치 오류: '+e.message; s.className='err'; },
    { enableHighAccuracy:true, maximumAge:5000, timeout:15000 });
  }
</script>
</body></html>"""


async def _index(_req: web.Request) -> web.Response:
    return web.Response(text=_PAGE, content_type="text/html")


async def _post_loc(req: web.Request) -> web.Response:
    try:
        data = await req.json()
        lat = float(data["lat"])
        lon = float(data["lon"])
        acc = data.get("accuracy")
        acc = float(acc) if acc is not None else None
    except (ValueError, KeyError, TypeError) as e:
        return web.json_response({"ok": False, "error": str(e)}, status=400)
    location.set_current(lat, lon, acc)
    return web.json_response({"ok": True})


async def _get_loc(req: web.Request) -> web.Response:
    """쿼리 파라미터로 좌표 수신 — GPSLogger·Tasker 등 백그라운드 앱용.

    예: GET /loc?lat=37.4979&lon=127.0276&accuracy=12
    (GPSLogger custom URL: .../loc?lat=%LAT&lon=%LON&accuracy=%ACC)
    """
    q = req.query
    try:
        lat = float(q["lat"])
        lon = float(q["lon"])
        acc = float(q["accuracy"]) if q.get("accuracy") else None
    except (ValueError, KeyError, TypeError) as e:
        return web.Response(text=f"need lat & lon ({e})", status=400)
    location.set_current(lat, lon, acc)
    return web.Response(text="OK")


async def start_location_server(port: int = 8765) -> web.AppRunner:
    """봇 시작 시 1회 호출. 같은 이벤트 루프에 위치 수신 서버를 띄운다."""
    app = web.Application()
    app.router.add_get("/", _index)
    app.router.add_post("/loc", _post_loc)
    app.router.add_get("/loc", _get_loc)   # GPSLogger·Tasker 등 백그라운드 앱(쿼리 방식)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info("📍 위치 서버 시작 — 포트 %d (폰에서 cloudflared https URL로 접속)", port)
    return runner
