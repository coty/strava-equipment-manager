from pydantic import BaseModel
from datetime import datetime


class RuleConditionBase(BaseModel):
    field: str
    operator: str
    value: str
    logic: str = "AND"


class RuleConditionCreate(RuleConditionBase):
    pass


class RuleConditionResponse(RuleConditionBase):
    id: int

    class Config:
        from_attributes = True


class RuleBase(BaseModel):
    name: str
    priority: int = 0
    is_active: bool = True


class RuleCreate(RuleBase):
    target_gear_id: int
    conditions: list[RuleConditionCreate]


class RuleUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    target_gear_id: int | None = None
    is_active: bool | None = None
    conditions: list[RuleConditionCreate] | None = None


class RuleResponse(RuleBase):
    id: int
    user_id: int
    target_gear_id: int
    target_gear_name: str | None = None
    conditions: list[RuleConditionResponse]
    matching_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RulePreviewActivity(BaseModel):
    id: int
    strava_activity_id: int
    name: str
    activity_type: str
    start_date: datetime
    distance: float
    moving_time: int
    current_gear_id: int | None
    current_gear_name: str | None
    new_gear_id: int
    new_gear_name: str


class RulePreviewResponse(BaseModel):
    rule_id: int
    rule_name: str
    target_gear_id: int
    target_gear_name: str
    matching_activities: list[RulePreviewActivity]
    total_count: int
