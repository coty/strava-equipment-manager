from app.routers.auth import router as auth_router
from app.routers.activities import router as activities_router
from app.routers.equipment import router as equipment_router
from app.routers.rules import router as rules_router

__all__ = ["auth_router", "activities_router", "equipment_router", "rules_router"]
