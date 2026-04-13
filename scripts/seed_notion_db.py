#!/usr/bin/env python3
"""Creates the required Notion database schema for voice assistant notes."""
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import httpx
from core.config import get_settings

BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def find_or_create_database(api_key: str, parent_page_id: str | None = None) -> str:
    """Search for existing 'Voice Notes' database or create it."""
    async with httpx.AsyncClient() as client:
        # Search for existing database
        resp = await client.post(
            f"{BASE_URL}/search",
            json={"query": "Voice Notes", "filter": {"value": "database", "property": "object"}},
            headers=headers(api_key),
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            db_id = results[0]["id"]
            print(f"Found existing 'Voice Notes' database: {db_id}")
            return db_id

        if not parent_page_id:
            print(
                "ERROR: No 'Voice Notes' database found and no parent page ID provided.\n"
                "Run with: python seed_notion_db.py --parent-page-id YOUR_PAGE_ID\n"
                "The page ID is the 32-char hex ID in the Notion page URL."
            )
            sys.exit(1)

        # Create database
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "Voice Notes"}}],
            "properties": {
                "Name": {"title": {}},
                "Created": {"date": {}},
                "Tags": {
                    "multi_select": {
                        "options": [
                            {"name": "task", "color": "blue"},
                            {"name": "meeting", "color": "green"},
                            {"name": "idea", "color": "yellow"},
                            {"name": "reminder", "color": "red"},
                        ]
                    }
                },
                "Source": {
                    "select": {
                        "options": [
                            {"name": "voice", "color": "purple"},
                            {"name": "manual", "color": "gray"},
                        ]
                    }
                },
            },
        }
        resp = await client.post(f"{BASE_URL}/databases", json=payload, headers=headers(api_key))
        resp.raise_for_status()
        db = resp.json()
        db_id = db["id"]
        print(f"Created 'Voice Notes' database: {db_id}")
        print(f"\nAdd to your .env:\nNOTION_NOTES_DATABASE_ID={db_id}")
        return db_id


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed Notion database for voice notes")
    parser.add_argument("--parent-page-id", help="Notion page ID to create the database under")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.notion_api_key:
        print("ERROR: NOTION_API_KEY not set in .env")
        sys.exit(1)

    db_id = await find_or_create_database(
        api_key=settings.notion_api_key,
        parent_page_id=args.parent_page_id,
    )

    if settings.notion_notes_database_id:
        print(f"\nCurrent NOTION_NOTES_DATABASE_ID in .env: {settings.notion_notes_database_id}")
        if settings.notion_notes_database_id != db_id.replace("-", ""):
            print(f"Update .env to: NOTION_NOTES_DATABASE_ID={db_id}")
    else:
        print(f"\nSet in .env:\nNOTION_NOTES_DATABASE_ID={db_id}")


if __name__ == "__main__":
    asyncio.run(main())
