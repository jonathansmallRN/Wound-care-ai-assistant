from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://wound_care:wound_care@db:5432/wound_care"

    mock_ai_mode: bool = True
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1"

    media_root: str = "/app/media"
    media_base_url: str = "http://localhost:8000/media"

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
