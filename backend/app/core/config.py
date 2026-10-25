from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic import field_validator


class Settings(BaseSettings):
    app_name: str = "aquaData API"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str = "postgresql+psycopg://aquadata:aquadata@localhost:5432/aquadata"
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()