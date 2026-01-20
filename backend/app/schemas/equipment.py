from pydantic import BaseModel
from datetime import datetime


class EquipmentBase(BaseModel):
    name: str
    equipment_type: str
    brand_name: str | None = None
    model_name: str | None = None
    description: str | None = None


class EquipmentCreate(EquipmentBase):
    strava_gear_id: str
    distance: float = 0
    is_primary: bool = False
    is_retired: bool = False


class EquipmentResponse(EquipmentBase):
    id: int
    strava_gear_id: str
    user_id: int
    distance: float
    is_primary: bool
    is_retired: bool
    synced_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class EquipmentStats(BaseModel):
    id: int
    name: str
    equipment_type: str
    brand_name: str | None = None
    model_name: str | None = None
    description: str | None = None
    distance: float
    is_primary: bool = False
    is_retired: bool = False
    activity_count: int
    total_time: int  # seconds
    last_used: datetime | None

    class Config:
        from_attributes = True
