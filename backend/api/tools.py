from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from core.auth import verify_elevenlabs_secret
from services import todoist, google_calendar, notion, memory

router = APIRouter(prefix="/tools")


# ─── Request models ───────────────────────────────────────────────────────────

class CreateTaskBody(BaseModel):
    title: str
    due: Optional[str] = None          # Natural language or ISO date string
    priority: Optional[int] = None     # 1 (urgent) – 4 (normal) per Todoist convention
    description: Optional[str] = None


class CreateEventBody(BaseModel):
    title: str
    start: str                          # ISO 8601 datetime string
    end: Optional[str] = None          # Defaults to start + 1 hour
    description: Optional[str] = None
    attendees: Optional[list[str]] = None   # List of email addresses


class CreateNoteBody(BaseModel):
    title: str
    content: str
    tags: Optional[list[str]] = None


class MemoryStoreBody(BaseModel):
    session_id: str
    transcript: str
    action_taken: Optional[str] = None
    result_summary: Optional[str] = None
    timestamp: Optional[str] = None


class MemoryGetBody(BaseModel):
    session_id: str


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/create-task")
async def create_task(body: CreateTaskBody, _: None = Depends(verify_elevenlabs_secret)):
    result = await todoist.create_task(
        title=body.title,
        due=body.due,
        priority=body.priority,
        description=body.description,
    )
    return result


@router.post("/create-event")
async def create_event(body: CreateEventBody, _: None = Depends(verify_elevenlabs_secret)):
    result = await google_calendar.create_event(
        title=body.title,
        start=body.start,
        end=body.end,
        description=body.description,
        attendees=body.attendees,
    )
    return result


@router.post("/create-note")
async def create_note(body: CreateNoteBody, _: None = Depends(verify_elevenlabs_secret)):
    result = await notion.create_note(
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    return result


@router.get("/list-tasks")
async def list_tasks(
    filter: Optional[str] = "today",
    _: None = Depends(verify_elevenlabs_secret),
):
    result = await todoist.list_tasks(filter=filter)
    return result


@router.get("/list-events")
async def list_events(
    days_ahead: int = 7,
    _: None = Depends(verify_elevenlabs_secret),
):
    result = await google_calendar.list_events(days_ahead=days_ahead)
    return result


@router.post("/memory/store")
async def memory_store(body: MemoryStoreBody, _: None = Depends(verify_elevenlabs_secret)):
    payload = {
        "session_id": body.session_id,
        "transcript": body.transcript,
        "action_taken": body.action_taken,
        "result_summary": body.result_summary,
        "timestamp": body.timestamp or datetime.now(timezone.utc).isoformat(),
    }
    result = await memory.store(payload)
    return result


@router.post("/memory/get")
async def memory_get(body: MemoryGetBody, _: None = Depends(verify_elevenlabs_secret)):
    result = await memory.retrieve(session_id=body.session_id)
    return result
