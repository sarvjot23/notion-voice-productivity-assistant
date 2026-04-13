"""n8n webhook client for persistent cross-session memory."""
from core.config import get_settings
from core.http import make_client


def _headers() -> dict:
    settings = get_settings()
    secret = settings.n8n_webhook_secret
    h = {"Content-Type": "application/json"}
    if secret:
        h["X-N8N-Secret"] = secret
    return h


def _base_url() -> str:
    return get_settings().n8n_base_url.rstrip("/")


async def store(payload: dict) -> dict:
    """Fire-and-forget store — best-effort, non-blocking on failure."""
    settings = get_settings()
    url = _base_url() + settings.n8n_memory_store_path
    try:
        async with make_client(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=_headers())
            resp.raise_for_status()
            return {"success": True}
    except Exception as exc:
        # Degrade gracefully — memory failure must not break tool calls
        return {"success": False, "error": str(exc)}


async def retrieve(session_id: str) -> dict:
    """Blocking retrieve — returns recent turns for the given session."""
    settings = get_settings()
    url = _base_url() + settings.n8n_memory_retrieve_path
    try:
        async with make_client(timeout=5.0) as client:
            resp = await client.post(
                url, json={"session_id": session_id}, headers=_headers()
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        return {"recent_turns": [], "error": str(exc)}
