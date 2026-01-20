from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Strava OAuth
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8000/api/auth/callback"

    # Application
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite+aiosqlite:///./strava_equipment.db"
    frontend_url: str = "http://localhost:5173"

    # Strava API
    strava_auth_url: str = "https://www.strava.com/oauth/authorize"
    strava_token_url: str = "https://www.strava.com/oauth/token"
    strava_api_base: str = "https://www.strava.com/api/v3"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
