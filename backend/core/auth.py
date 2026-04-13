from fastapi import Header, HTTPException, status
from .config import get_settings


async def verify_elevenlabs_secret(x_elevenlabs_secret: str = Header(default="")) -> None:
    """Validates that the request originates from the ElevenLabs agent."""
    settings = get_settings()
    expected = settings.elevenlabs_webhook_secret

    # If no secret is configured, skip validation (dev mode)
    if not expected:
        return

    if x_elevenlabs_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ElevenLabs webhook secret",
        )
