from pydantic import BaseModel
from datetime import datetime


class ActivityBase(BaseModel):
    name: str
    activity_type: str
    sport_type: str | None = None
    start_date: datetime
    distance: float
    moving_time: int
    elapsed_time: int
    trainer: bool = False
    device_name: str | None = None
    external_id: str | None = None


class ActivityResponse(ActivityBase):
    id: int
    strava_activity_id: int
    user_id: int
    gear_id: int | None
    strava_gear_id: str | None
    total_elevation_gain: float | None
    average_speed: float | None
    max_speed: float | None
    commute: bool
    manual: bool
    private: bool
    synced_at: datetime
    created_at: datetime

    # Include equipment name for convenience
    gear_name: str | None = None

    class Config:
        from_attributes = True


class ActivityFilter(BaseModel):
    search: str | None = None
    activity_type: str | None = None
    equipment_id: int | None = None
    trainer: bool | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    limit: int = 50
    offset: int = 0


class ActivityUpdate(BaseModel):
    gear_id: int | None = None


class ActivityBulkUpdate(BaseModel):
    activity_ids: list[int]
    gear_id: int
