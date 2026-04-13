#!/usr/bin/env python3
"""Integration tests — hits each service directly to verify credentials and connectivity.

Usage:
    cd backend
    python ../scripts/test_pipeline.py [--service todoist|gcal|notion|memory|all]
"""
import os
import sys
import asyncio
import argparse
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
SKIP = "\033[93m–\033[0m"


def result(ok: bool | None, label: str, detail: str = ""):
    icon = PASS if ok else (SKIP if ok is None else FAIL)
    suffix = f"  ({detail})" if detail else ""
    print(f"  {icon} {label}{suffix}")


async def test_todoist():
    print("\n[Todoist]")
    from services.todoist import create_task, list_tasks
    from core.config import get_settings

    if not get_settings().todoist_api_token:
        result(None, "Skipped — TODOIST_API_TOKEN not set")
        return

    try:
        r = await create_task(title="[Test] Voice assistant ping", due="tomorrow", priority=4)
        result(True, "create_task", f"id={r['task_id']}")
    except Exception as e:
        result(False, "create_task", str(e))

    try:
        r = await list_tasks(filter="today")
        result(True, "list_tasks", f"{r['count']} tasks today")
    except Exception as e:
        result(False, "list_tasks", str(e))


async def test_gcal():
    print("\n[Google Calendar]")
    from services.google_calendar import create_event, list_events
    from core.config import get_settings

    if not os.path.exists(get_settings().google_token_file):
        result(None, "Skipped — run scripts/setup_google_oauth.py first")
        return

    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    try:
        r = await create_event(
            title="[Test] Voice assistant ping",
            start=start.isoformat(),
            description="Auto-generated test event",
        )
        result(True, "create_event", f"id={r['event_id']}")
    except Exception as e:
        result(False, "create_event", str(e))

    try:
        r = await list_events(days_ahead=7)
        result(True, "list_events", f"{r['count']} events next 7 days")
    except Exception as e:
        result(False, "list_events", str(e))


async def test_notion():
    print("\n[Notion]")
    from services.notion import create_note
    from core.config import get_settings

    s = get_settings()
    if not s.notion_api_key or not s.notion_notes_database_id:
        result(None, "Skipped — NOTION_API_KEY or NOTION_NOTES_DATABASE_ID not set")
        return

    try:
        r = await create_note(
            title="[Test] Voice assistant ping",
            content="Auto-generated test note from test_pipeline.py",
            tags=["test"],
        )
        result(True, "create_note", f"id={r['page_id']}")
    except Exception as e:
        result(False, "create_note", str(e))


async def test_memory():
    print("\n[Memory / n8n]")
    from services.memory import store, retrieve

    session_id = f"test-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    try:
        r = await store({
            "session_id": session_id,
            "transcript": "test pipeline check",
            "action_taken": "test_pipeline",
            "result_summary": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if r.get("success"):
            result(True, "memory_store")
        else:
            result(False, "memory_store", r.get("error", "unknown"))
    except Exception as e:
        result(False, "memory_store", str(e))

    try:
        r = await retrieve(session_id=session_id)
        turns = r.get("recent_turns", [])
        if "error" in r and not turns:
            result(False, "memory_retrieve", r["error"])
        else:
            result(True, "memory_retrieve", f"{len(turns)} turn(s) returned")
    except Exception as e:
        result(False, "memory_retrieve", str(e))


async def test_health():
    print("\n[Backend Health]")
    import httpx
    from core.config import get_settings

    s = get_settings()
    url = f"http://localhost:{s.port}/health"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=3.0)
            resp.raise_for_status()
            result(True, "GET /health", resp.text.strip())
    except Exception as e:
        result(False, "GET /health", f"{e} — is the backend running?")


async def main():
    parser = argparse.ArgumentParser(description="Integration test suite")
    parser.add_argument(
        "--service",
        choices=["todoist", "gcal", "notion", "memory", "health", "all"],
        default="all",
        help="Which service to test (default: all)",
    )
    args = parser.parse_args()

    print("Voice Productivity Assistant — Integration Test")
    print("=" * 50)

    svc = args.service
    if svc in ("health", "all"):
        await test_health()
    if svc in ("todoist", "all"):
        await test_todoist()
    if svc in ("gcal", "all"):
        await test_gcal()
    if svc in ("notion", "all"):
        await test_notion()
    if svc in ("memory", "all"):
        await test_memory()

    print()


if __name__ == "__main__":
    asyncio.run(main())
