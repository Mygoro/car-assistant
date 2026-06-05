"""Google Calendar native tool — CRUD operations.

Reuses google_credentials.json from the lecture-note automation project.
Token file is stored locally at core/native_tools/calendar_token.json.
"""
import asyncio
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
_SCOPES = ["https://www.googleapis.com/auth/calendar"]

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


def _to_kst(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
    return dt


async def get_calendar_events(args: dict) -> str:
    """Google Calendar 일정 조회.

    args:
        start_date: ISO date string, e.g. "2026-06-02" (기본: 오늘)
        end_date:   ISO date string (기본: start_date + 7일)
    """
    start_str = args.get("start_date")
    end_str = args.get("end_date")

    now_kst = datetime.now(timezone(timedelta(hours=9)))
    today_str = now_kst.strftime("%Y-%m-%d")
    if start_str:
        start_dt = _to_kst(start_str)
        if start_str == today_str:
            start_dt = now_kst
    else:
        start_dt = now_kst

    if end_str:
        end_dt = _to_kst(end_str)
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(days=1)
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
            ev_id = ev.get("id", "")
            lines.append(f"- [{ev_id}] {start}: {summary}{loc_str}")
        return "\n".join(lines)

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    except Exception as e:
        log.error("Calendar fetch error: %s", e)
        return f"[Calendar error: {e}]"


async def create_calendar_event(args: dict) -> str:
    """Google Calendar 일정 생성.

    args:
        summary:    일정 제목 (필수)
        start:      시작 시각, ISO datetime string e.g. "2026-06-10T15:00:00" (필수)
        end:        종료 시각, ISO datetime string (기본: start + 1시간)
        location:   장소 (선택)
        description: 메모 (선택)
    """
    summary = args.get("summary")
    if not summary:
        return "[Calendar error: summary 필드가 필요합니다]"

    start_str = args.get("start")
    if not start_str:
        return "[Calendar error: start 필드가 필요합니다]"

    start_dt = _to_kst(start_str)
    end_str = args.get("end")
    end_dt = _to_kst(end_str) if end_str else start_dt + timedelta(hours=1)

    body = {
        "summary": summary,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Seoul"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Seoul"},
    }
    if args.get("location"):
        body["location"] = args["location"]
    if args.get("description"):
        body["description"] = args["description"]

    def _create():
        svc = _build_service()
        ev = svc.events().insert(calendarId="primary", body=body).execute()
        return f"일정 생성 완료: [{ev['id']}] {ev['summary']} ({ev['start'].get('dateTime', '')})"

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _create)
    except Exception as e:
        log.error("Calendar create error: %s", e)
        return f"[Calendar error: {e}]"


async def update_calendar_event(args: dict) -> str:
    """Google Calendar 일정 수정.

    args:
        event_id:    수정할 이벤트 ID (get_calendar_events 결과의 [id]) (필수)
        summary:     새 제목 (선택)
        start:       새 시작 시각 ISO datetime string (선택)
        end:         새 종료 시각 ISO datetime string (선택)
        location:    새 장소 (선택)
        description: 새 메모 (선택)
    """
    event_id = args.get("event_id")
    if not event_id:
        return "[Calendar error: event_id 필드가 필요합니다]"

    def _update():
        svc = _build_service()
        ev = svc.events().get(calendarId="primary", eventId=event_id).execute()

        if args.get("summary"):
            ev["summary"] = args["summary"]
        if args.get("start"):
            ev["start"] = {"dateTime": _to_kst(args["start"]).isoformat(), "timeZone": "Asia/Seoul"}
        if args.get("end"):
            ev["end"] = {"dateTime": _to_kst(args["end"]).isoformat(), "timeZone": "Asia/Seoul"}
        if args.get("location"):
            ev["location"] = args["location"]
        if args.get("description"):
            ev["description"] = args["description"]

        updated = svc.events().update(calendarId="primary", eventId=event_id, body=ev).execute()
        return f"일정 수정 완료: [{updated['id']}] {updated['summary']} ({updated['start'].get('dateTime', '')})"

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _update)
    except Exception as e:
        log.error("Calendar update error: %s", e)
        return f"[Calendar error: {e}]"


async def delete_calendar_event(args: dict) -> str:
    """Google Calendar 일정 삭제.

    args:
        event_id: 삭제할 이벤트 ID (get_calendar_events 결과의 [id]) (필수)
    """
    event_id = args.get("event_id")
    if not event_id:
        return "[Calendar error: event_id 필드가 필요합니다]"

    def _delete():
        svc = _build_service()
        svc.events().delete(calendarId="primary", eventId=event_id).execute()
        return f"일정 삭제 완료: {event_id}"

    try:
        return await asyncio.get_event_loop().run_in_executor(None, _delete)
    except Exception as e:
        log.error("Calendar delete error: %s", e)
        return f"[Calendar error: {e}]"
