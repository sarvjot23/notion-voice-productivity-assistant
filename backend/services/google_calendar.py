"""Google Calendar API v3 wrapper."""
import os
import certifi
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from core.config import get_settings

# Point Python's SSL to certifi's CA bundle (fixes SSL on Windows)
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    settings = get_settings()
    token_file = settings.google_token_file

    if not os.path.exists(token_file):
        raise RuntimeError(
            f"Google token file not found: {token_file}. "
            "Run scripts/setup_google_oauth.py first."
        )

    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # Persist refreshed token
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def _parse_datetime(dt_str: str) -> str:
    """Ensure ISO 8601 with timezone for Google Calendar."""
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return dt_str


async def create_event(
    title: str,
    start: str,
    end: str | None = None,
    description: str | None = None,
    attendees: list[str] | None = None,
) -> dict:
    start_dt = _parse_datetime(start)
    if end:
        end_dt = _parse_datetime(end)
    else:
        # Default: 1 hour after start
        end_dt = (datetime.fromisoformat(start_dt) + timedelta(hours=1)).isoformat()

    event_body: dict = {
        "summary": title,
        "start": {"dateTime": start_dt, "timeZone": "UTC"},
        "end": {"dateTime": end_dt, "timeZone": "UTC"},
    }
    if description:
        event_body["description"] = description
    if attendees:
        event_body["attendees"] = [{"email": e} for e in attendees]

    service = _get_service()
    event = service.events().insert(calendarId="primary", body=event_body).execute()

    return {
        "event_id": event["id"],
        "html_link": event.get("htmlLink", ""),
        "confirmation": f"Event '{title}' scheduled on your calendar.",
    }


async def list_events(days_ahead: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    service = _get_service()
    result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        )
        .execute()
    )

    events = result.get("items", [])
    items = [
        {
            "id": e["id"],
            "title": e.get("summary", "(no title)"),
            "start": e["start"].get("dateTime", e["start"].get("date")),
            "end": e["end"].get("dateTime", e["end"].get("date")),
        }
        for e in events
    ]
    return {"events": items, "count": len(items)}
