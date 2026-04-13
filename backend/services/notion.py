"""Notion API wrapper — creates pages in the configured notes database."""
from datetime import datetime, timezone
from core.config import get_settings
from core.http import make_client

BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {get_settings().notion_api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


import re


def _rich_text(text: str) -> list:
    return [{"type": "text", "text": {"content": text[:2000]}}]


def _parse_line(line: str) -> dict:
    """Convert a markdown-style line into the correct Notion block type."""
    # Checklist: - [ ] or - [x]
    m = re.match(r"^- \[(x| )\] (.+)", line)
    if m:
        return {
            "type": "to_do",
            "to_do": {
                "rich_text": _rich_text(m.group(2)),
                "checked": m.group(1) == "x",
            },
        }

    # Bulleted list: - item or * item
    m = re.match(r"^[-*] (.+)", line)
    if m:
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": _rich_text(m.group(1))},
        }

    # Numbered list: 1. item  or  1) item
    m = re.match(r"^\d+[.)]\s+(.+)", line)
    if m:
        return {
            "type": "numbered_list_item",
            "numbered_list_item": {"rich_text": _rich_text(m.group(1))},
        }

    # Heading: ## or #
    m = re.match(r"^(#{1,3}) (.+)", line)
    if m:
        level = len(m.group(1))
        htype = f"heading_{level}"
        return {
            "type": htype,
            htype: {"rich_text": _rich_text(m.group(2))},
        }

    # Default: paragraph
    return {
        "type": "paragraph",
        "paragraph": {"rich_text": _rich_text(line) if line.strip() else []},
    }


def _content_to_blocks(content: str) -> list:
    blocks = []
    for line in content.splitlines():
        blocks.append(_parse_line(line))
    return blocks or [{"type": "paragraph", "paragraph": {"rich_text": []}}]


async def create_note(
    title: str,
    content: str,
    tags: list[str] | None = None,
) -> dict:
    settings = get_settings()
    database_id = settings.notion_notes_database_id

    properties: dict = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Created": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
    }
    if tags:
        properties["Tags"] = {"multi_select": [{"name": t} for t in tags]}

    blocks = _content_to_blocks(content)

    payload = {
        "parent": {"database_id": database_id},
        "properties": properties,
        "children": blocks,
    }

    async with make_client() as client:
        resp = await client.post(f"{BASE_URL}/pages", json=payload, headers=_headers())
        resp.raise_for_status()
        page = resp.json()

    url = page.get("url", "")
    return {
        "page_id": page["id"],
        "url": url,
        "confirmation": f"Note '{title}' saved to Notion.",
    }
