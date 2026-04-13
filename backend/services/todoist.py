"""Todoist REST API v2 wrapper."""
from core.config import get_settings
from core.http import make_client

BASE_URL = "https://api.todoist.com/rest/v2"

# Priority mapping: user-facing (1=urgent) → Todoist API (4=urgent, 1=normal)
_PRIORITY_MAP = {1: 4, 2: 3, 3: 2, 4: 1}


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_settings().todoist_api_token}"}


async def create_task(
    title: str,
    due: str | None = None,
    priority: int | None = None,
    description: str | None = None,
) -> dict:
    payload: dict = {"content": title}
    if due:
        payload["due_string"] = due
    if priority is not None:
        payload["priority"] = _PRIORITY_MAP.get(priority, 1)
    if description:
        payload["description"] = description

    async with make_client() as client:
        resp = await client.post(f"{BASE_URL}/tasks", json=payload, headers=_headers())
        resp.raise_for_status()
        task = resp.json()

    return {
        "task_id": task["id"],
        "url": task.get("url", ""),
        "confirmation": f"Task '{title}' created in Todoist.",
    }


async def list_tasks(filter: str = "today") -> dict:
    params = {"filter": filter}
    async with make_client() as client:
        resp = await client.get(f"{BASE_URL}/tasks", params=params, headers=_headers())
        resp.raise_for_status()
        tasks = resp.json()

    items = [
        {
            "id": t["id"],
            "title": t["content"],
            "due": t.get("due", {}).get("string") if t.get("due") else None,
            "priority": t.get("priority", 1),
        }
        for t in tasks
    ]
    return {"tasks": items, "count": len(items)}
