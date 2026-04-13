from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_agent_id: str = ""
    elevenlabs_webhook_secret: str = ""

    # Todoist
    todoist_api_token: str = ""

    # Google Calendar
    google_client_id: str = ""
    google_client_secret: str = ""
    google_token_file: str = ".google_token.json"

    # Notion
    notion_api_key: str = ""
    notion_notes_database_id: str = ""

    # n8n
    n8n_base_url: str = "http://localhost:5678"
    n8n_memory_store_path: str = "/webhook/memory/store"
    n8n_memory_retrieve_path: str = "/webhook/memory/retrieve"
    n8n_webhook_secret: str = ""
    n8n_password: str = ""

    # Backend
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
