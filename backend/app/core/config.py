from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "aquaData API"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str = "postgresql+psycopg://aquadata:aquadata@localhost:5432/aquadata"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()