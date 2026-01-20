from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract

from app.database import get_db
from app.models.user import User
from app.models.equipment import Equipment
from app.models.activity import Activity
from app.schemas.equipment import EquipmentResponse, EquipmentStats
from app.routers.auth import get_current_user
from app.services.strava import StravaService

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=list[EquipmentResponse])
async def get_equipment(
    include_retired: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all equipment for the current user."""
    query = select(Equipment).where(Equipment.user_id == user.id)

    if not include_retired:
        query = query.where(Equipment.is_retired == False)

    query = query.order_by(Equipment.equipment_type, Equipment.name)

    result = await db.execute(query)
    equipment = result.scalars().all()

    return [EquipmentResponse.model_validate(eq) for eq in equipment]


@router.get("/stats", response_model=list[EquipmentStats])
async def get_equipment_stats(
    include_retired: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get equipment with usage statistics."""
    query = select(Equipment).where(Equipment.user_id == user.id)

    if not include_retired:
        query = query.where(Equipment.is_retired == False)

    result = await db.execute(query)
    equipment_list = result.scalars().all()

    stats = []
    for eq in equipment_list:
        # Get activity stats
        activity_query = select(
            func.count(Activity.id).label("count"),
            func.sum(Activity.moving_time).label("total_time"),
            func.max(Activity.start_date).label("last_used"),
        ).where(Activity.gear_id == eq.id)

        activity_result = await db.execute(activity_query)
        activity_stats = activity_result.one()

        stats.append(
            EquipmentStats(
                id=eq.id,
                name=eq.name,
                equipment_type=eq.equipment_type,
                brand_name=eq.brand_name,
                model_name=eq.model_name,
                description=eq.description,
                distance=eq.distance,
                is_primary=eq.is_primary,
                is_retired=eq.is_retired,
                activity_count=activity_stats.count or 0,
                total_time=activity_stats.total_time or 0,
                last_used=activity_stats.last_used,
            )
        )

    return stats


@router.get("/usage-history")
async def get_equipment_usage_history(
    months: int = Query(6, le=12),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get monthly equipment usage history for charts."""
    # Get active equipment
    eq_result = await db.execute(
        select(Equipment)
        .where(Equipment.user_id == user.id, Equipment.is_retired == False)
    )
    equipment_list = eq_result.scalars().all()
    equipment_map = {eq.id: eq for eq in equipment_list}

    # Calculate date range
    now = datetime.utcnow()
    start_date = now - timedelta(days=months * 30)

    # Get activities in date range
    activities_result = await db.execute(
        select(Activity)
        .where(
            Activity.user_id == user.id,
            Activity.start_date >= start_date,
            Activity.gear_id.isnot(None),
        )
    )
    activities = activities_result.scalars().all()

    # Aggregate by month and equipment
    usage_data = defaultdict(lambda: defaultdict(float))

    for activity in activities:
        if activity.gear_id not in equipment_map:
            continue
        month_key = activity.start_date.strftime("%Y-%m")
        usage_data[activity.gear_id][month_key] += activity.distance / 1000  # Convert to km

    # Generate month labels for the range
    month_labels = []
    current = start_date.replace(day=1)
    while current <= now:
        month_labels.append(current.strftime("%Y-%m"))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    # Build response
    datasets = []
    for eq_id, eq in equipment_map.items():
        monthly_data = usage_data.get(eq_id, {})
        datasets.append({
            "equipment_id": eq_id,
            "equipment_name": eq.name,
            "equipment_type": eq.equipment_type,
            "data": [round(monthly_data.get(month, 0), 1) for month in month_labels]
        })

    return {
        "labels": month_labels,
        "datasets": datasets,
    }


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment_by_id(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific piece of equipment by ID."""
    result = await db.execute(
        select(Equipment).where(
            Equipment.id == equipment_id, Equipment.user_id == user.id
        )
    )
    equipment = result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return EquipmentResponse.model_validate(equipment)


@router.post("/sync")
async def sync_equipment(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sync equipment from Strava."""
    strava = StravaService(user.access_token)

    try:
        gear_list = await strava.get_all_gear()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch from Strava: {str(e)}"
        )

    synced_count = 0
    created_count = 0
    updated_count = 0

    for gear_data in gear_list:
        strava_gear_id = gear_data["id"]

        # Check if equipment exists
        result = await db.execute(
            select(Equipment).where(
                Equipment.strava_gear_id == strava_gear_id,
                Equipment.user_id == user.id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing equipment
            existing.name = gear_data.get("name", existing.name)
            existing.brand_name = gear_data.get("brand_name")
            existing.model_name = gear_data.get("model_name")
            existing.description = gear_data.get("description")
            existing.distance = gear_data.get("distance", 0)
            existing.is_primary = gear_data.get("primary", False)
            existing.is_retired = gear_data.get("retired", False)
            existing.equipment_type = gear_data.get("equipment_type", existing.equipment_type)
            existing.synced_at = datetime.utcnow()
            updated_count += 1
        else:
            # Create new equipment
            new_equipment = Equipment(
                strava_gear_id=strava_gear_id,
                user_id=user.id,
                name=gear_data.get("name", "Unknown"),
                equipment_type=gear_data.get("equipment_type", "unknown"),
                brand_name=gear_data.get("brand_name"),
                model_name=gear_data.get("model_name"),
                description=gear_data.get("description"),
                distance=gear_data.get("distance", 0),
                is_primary=gear_data.get("primary", False),
                is_retired=gear_data.get("retired", False),
            )
            db.add(new_equipment)
            created_count += 1

        synced_count += 1

    await db.commit()

    return {
        "message": "Sync completed",
        "synced": synced_count,
        "created": created_count,
        "updated": updated_count,
    }
