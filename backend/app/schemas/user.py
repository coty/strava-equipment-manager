from pydantic import BaseModel
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    strava_athlete_id: int
    firstname: str | None
    lastname: str | None
    profile: str | None
    city: str | None
    state: str | None
    country: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuthStatus(BaseModel):
    is_authenticated: bool
    user: UserResponse | None = None
