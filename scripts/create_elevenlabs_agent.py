#!/usr/bin/env python3
"""Creates or updates the ElevenLabs voice agent via the ElevenLabs API.

Usage:
    python create_elevenlabs_agent.py --backend-url https://<ngrok-id>.ngrok.io
    python create_elevenlabs_agent.py --backend-url https://your-production-host.com --update
"""
import os
import sys
import argparse
from datetime import date

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from core.config import get_settings

ELEVENLABS_API = "https://api.elevenlabs.io/v1"


SYSTEM_PROMPT_TEMPLATE = """You are a voice productivity assistant. Today's date is {today}.

You help the user manage tasks, calendar events, and notes through natural speech.
Be concise — spoken responses should be 1–2 sentences maximum.

At the start of each conversation, call memory_get with the current session_id to retrieve context.
After completing any action, call memory_store with a summary of what was done.

Guidelines:
- If the user mentions "task", "todo", or "remind me", call create_task.
- If the user mentions "meeting", "appointment", "schedule", or "calendar", call create_event.
- If the user says "note", "remember this", "write down", "checklist", "to-do list in Notion", or asks you to create/save any content to Notion, call create_note. Use markdown checkboxes (- [ ] item) in the content field for checklists.
- IMPORTANT: Always use your tools to take action. Never instruct the user to do something manually that you can do via a tool call.
- To read back pending work, call list_tasks or list_events as appropriate.
- Always confirm what you did in one short sentence, e.g. "Done — task added for Friday."
- If a required field (like a date/time) is missing, ask for it before calling the tool.
- Use a friendly, natural tone. Avoid filler phrases like "Certainly!" or "Of course!"."""


TOOLS = [
    {
        "name": "create_task",
        "description": "Create a task in Todoist",
        "type": "webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "due": {"type": "string", "description": "Due date/time (natural language or ISO)"},
                "priority": {"type": "integer", "description": "Priority: 1=urgent, 4=normal"},
                "description": {"type": "string", "description": "Optional task description"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "create_event",
        "description": "Create a Google Calendar event",
        "type": "webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start": {"type": "string", "description": "Start datetime (ISO 8601)"},
                "end": {"type": "string", "description": "End datetime (ISO 8601), defaults to start + 1 hour"},
                "description": {"type": "string", "description": "Optional event description"},
                "attendees": {
                    "type": "array",
                    "items": {"type": "string", "description": "Attendee email address"},
                    "description": "List of attendee email addresses",
                },
            },
            "required": ["title", "start"],
        },
    },
    {
        "name": "create_note",
        "description": "Save a note to Notion",
        "type": "webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Note title"},
                "content": {"type": "string", "description": "Note body/content"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string", "description": "Tag name"},
                    "description": "Optional tags (e.g. meeting, idea, reminder)",
                },
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List pending tasks from Todoist",
        "type": "webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Todoist filter string (e.g. 'today', 'overdue', 'p1')",
                    "default": "today",
                },
            },
        },
    },
    {
        "name": "list_events",
        "description": "List upcoming calendar events",
        "type": "webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead to look (default 7)",
                    "default": 7,
                },
            },
        },
    },
    {
        "name": "memory_get",
        "description": "Retrieve recent session context from memory",
        "type": "webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Unique session identifier"},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "memory_store",
        "description": "Store a turn summary to persistent memory",
        "type": "webhook",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Unique session identifier"},
                "transcript": {"type": "string", "description": "What the user said"},
                "action_taken": {"type": "string", "description": "Tool that was called"},
                "result_summary": {"type": "string", "description": "Brief summary of the outcome"},
            },
            "required": ["session_id", "transcript"],
        },
    },
]


def build_agent_config(backend_url: str, settings, include_llm: bool = True) -> dict:
    backend_url = backend_url.rstrip("/")
    today = date.today().isoformat()

    # Map tool names to backend endpoints
    endpoint_map = {
        "create_task": f"{backend_url}/tools/create-task",
        "create_event": f"{backend_url}/tools/create-event",
        "create_note": f"{backend_url}/tools/create-note",
        "list_tasks": f"{backend_url}/tools/list-tasks",
        "list_events": f"{backend_url}/tools/list-events",
        "memory_get": f"{backend_url}/tools/memory/get",
        "memory_store": f"{backend_url}/tools/memory/store",
    }

    # Build webhook tool shape expected by ElevenLabs API
    enriched_tools = []
    for tool in TOOLS:
        params = tool.get("parameters", {"type": "object", "properties": {}})
        api_schema = {
            "url": endpoint_map[tool["name"]],
            "method": "POST",
            "request_body_schema": {
                "type": "object",
                "description": tool["description"],
                "properties": params.get("properties", {}),
                "required": params.get("required", []),
            },
        }
        if settings.elevenlabs_webhook_secret:
            api_schema["request_headers"] = {"X-ElevenLabs-Secret": settings.elevenlabs_webhook_secret}
        enriched_tools.append({
            "name": tool["name"],
            "description": tool["description"],
            "type": "webhook",
            "api_schema": api_schema,
        })

    return {
        "name": "Voice Productivity Assistant",
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": SYSTEM_PROMPT_TEMPLATE.format(today=today),
                    **({"llm": "claude-sonnet-4-6"} if include_llm else {}),
                    "tools": enriched_tools,
                },
                "first_message": "Hey! I'm your voice assistant. What would you like to get done today?",
                "language": "en",
            },
            "tts": {
                "model_id": "eleven_turbo_v2",
            },
            "asr": {
                "quality": "high",
                "user_input_audio_format": "pcm_16000",
            },
            "turn": {
                "turn_timeout": 60,
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Create or update ElevenLabs voice agent")
    parser.add_argument("--backend-url", required=True, help="Public URL of your backend (e.g. https://xyz.ngrok.io)")
    parser.add_argument("--update", action="store_true", help="Update existing agent instead of creating new one")
    parser.add_argument("--agent-id", help="Agent ID to update (uses ELEVENLABS_AGENT_ID from .env if not specified)")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.elevenlabs_api_key:
        print("ERROR: ELEVENLABS_API_KEY not set in .env")
        sys.exit(1)

    print(f"DEBUG: using key starting with: {settings.elevenlabs_api_key[:8]}...")

    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
    }

    config = build_agent_config(args.backend_url, settings, include_llm=not args.update)

    agent_id = args.agent_id or settings.elevenlabs_agent_id

    with httpx.Client() as client:
        if args.update and agent_id:
            resp = client.patch(
                f"{ELEVENLABS_API}/convai/agents/{agent_id}",
                json=config,
                headers=headers,
            )
            if not resp.is_success:
                print(f"ERROR {resp.status_code}: {resp.text}")
                sys.exit(1)
            print(f"Agent updated: {agent_id}")
        else:
            resp = client.post(
                f"{ELEVENLABS_API}/convai/agents/create",
                json=config,
                headers=headers,
            )
            if not resp.is_success:
                print(f"ERROR {resp.status_code}: {resp.text}")
                sys.exit(1)
            data = resp.json()
            agent_id = data.get("agent_id", data.get("id", ""))
            print(f"Agent created: {agent_id}")
            print(f"\nAdd to your .env:\nELEVENLABS_AGENT_ID={agent_id}")

    print("\nDone. Tool endpoints configured:")
    backend_url = args.backend_url.rstrip("/")
    for tool in TOOLS:
        endpoint = backend_url + "/tools/" + tool["name"].replace("_", "-")
        print(f"  {tool['name']:20s} → {endpoint}")


if __name__ == "__main__":
    main()
