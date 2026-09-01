"""
Application configuration, loaded from environment variables / .env.

Stage 1 only needs DATABASE_URL and CORS_ORIGINS, but this is where every
future setting (e.g. Neon connection string, feature flags) will live.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # postgresql://user:password@host:port/dbname
    database_url: str = "postgresql://cs348:cs348@localhost:5432/cs348"

    # Comma-separated list of allowed origins for CORS, e.g.
    # "http://localhost:5173,http://127.0.0.1:5173"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
