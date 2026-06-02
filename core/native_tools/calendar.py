"""Google Calendar native tool — get_calendar_events.

Reuses google_credentials.json from the lecture-note automation project.
Token file is stored locally at core/native_tools/calendar_token.json.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)

_CREDENTIALS_CANDIDATES = [
    Path("core/native_tools/google_credentials.json"),
    Path(__file__).parent.parent.parent.parent.parent
    / "lecture_notes"
    / "automation"
    / "google_credentials.json",
]
_TOKEN_FILE = Path("core/native_tools/calendar_token.json")
_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

_service = None


def _build_service():
    global _service
    if _service is not None:
        return _service

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if _TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_FILE), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cred_file = next((p for p in _CREDENTIALS_CANDIDATES if p.exists()), None)
            if cred_file is None:
                raise FileNotFoundError(
                    "google_credentials.json을 찾을 수 없습니다. "
                    "core/native_tools/google_credentials.json에 복사하거나 "
                    "강의노트 automation 폴더 경로를 확인하세요."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), _SCOPES)
            creds = flow.run_local_server(port=0)

        _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    _service = build("calendar", "v3", credentials=creds)
    return _service


async def get_calendar_events(args: dict) -> str:
    """Google Calendar 일정 조회.

    args:
        start_date: ISO date string, e.g. "2026-06-02" (기본: 오늘)
        end_date:   ISO date string (기본: start_date + 7일)
    """
    import asyncio

    start_str = args.get("start_date")
    end_str = args.get("end_date")

    now_kst = datetime.now(timezone(timedelta(hours=9)))
    if start_str:
        start_dt = datetime.fromisoformat(start_str).replace(
            tzinfo=timezone(timedelta(hours=9))
        )
    else:
        start_dt = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)

    if end_str:
        end_dt = datetime.fromisoformat(end_str).replace(
            tzinfo=timezone(timedelta(hours=9))
        )
    else:
        end_dt = start_dt + timedelta(days=7)

    def _fetch():
        svc = _build_service()
        result = (
            svc.events()
            .list(
                calendarId="primary",
                timeMin=start_dt.isoformat(),
                timeMax=end_dt.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=20,
            )
            .execute()
        )
        items = result.get("items", [])
        if not items:
            return "해당 기간에 일정이 없습니다."

        lines = []
        for ev in items:
            start = ev["start"].get("dateTime", ev["start"].get("date", ""))
            summary = ev.get("summary", "(제목 없음)")
            location = ev.get("location", "")
            loc_str = f" ({location})" if location else ""
            lines.append(f"- {start}: {summary}{loc_str}")
        return "\n".join(lines)

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    except Exception as e:
        log.error("Calendar fetch error: %s", e)
        return f"[Calendar error: {e}]"
