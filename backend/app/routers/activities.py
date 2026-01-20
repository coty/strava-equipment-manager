import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db, async_session
from app.models.user import User
from app.models.activity import Activity
from app.models.equipment import Equipment
from app.schemas.activity import ActivityResponse, ActivityFilter, ActivityUpdate, ActivityBulkUpdate
from app.routers.auth import get_current_user
from app.services.strava import StravaService

router = APIRouter(prefix="/activities", tags=["activities"])

# In-memory backfill status tracking (per user)
backfill_status: dict[int, dict] = {}


@router.get("/stats")
async def get_activity_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get activity statistics for the current user."""
    # Total count
    count_result = await db.execute(
        select(func.count(Activity.id)).where(Activity.user_id == user.id)
    )
    total_count = count_result.scalar() or 0

    # Total distance and time
    stats_result = await db.execute(
        select(
            func.sum(Activity.distance).label("total_distance"),
            func.sum(Activity.moving_time).label("total_time"),
        ).where(Activity.user_id == user.id)
    )
    stats = stats_result.one()

    return {
        "total_activities": total_count,
        "total_distance": stats.total_distance or 0,
        "total_time": stats.total_time or 0,
    }


@router.get("", response_model=list[ActivityResponse])
async def get_activities(
    search: str | None = None,
    activity_type: str | None = None,
    equipment_id: int | None = None,
    trainer: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get activities with optional filters."""
    query = (
        select(Activity)
        .where(Activity.user_id == user.id)
        .order_by(Activity.start_date.desc())
    )

    # Apply filters
    if search:
        query = query.where(Activity.name.ilike(f"%{search}%"))
    if activity_type:
        query = query.where(Activity.activity_type == activity_type)
    if equipment_id:
        query = query.where(Activity.gear_id == equipment_id)
    if trainer is not None:
        query = query.where(Activity.trainer == trainer)
    if date_from:
        query = query.where(Activity.start_date >= date_from)
    if date_to:
        query = query.where(Activity.start_date <= date_to)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    activities = result.scalars().all()

    # Get equipment names
    response = []
    for activity in activities:
        activity_dict = ActivityResponse.model_validate(activity).model_dump()
        if activity.gear_id:
            eq_result = await db.execute(
                select(Equipment).where(Equipment.id == activity.gear_id)
            )
            equipment = eq_result.scalar_one_or_none()
            activity_dict["gear_name"] = equipment.name if equipment else None
        response.append(ActivityResponse(**activity_dict))

    return response


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific activity by ID."""
    result = await db.execute(
        select(Activity).where(
            Activity.id == activity_id, Activity.user_id == user.id
        )
    )
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity_dict = ActivityResponse.model_validate(activity).model_dump()
    if activity.gear_id:
        eq_result = await db.execute(
            select(Equipment).where(Equipment.id == activity.gear_id)
        )
        equipment = eq_result.scalar_one_or_none()
        activity_dict["gear_name"] = equipment.name if equipment else None

    return ActivityResponse(**activity_dict)


@router.patch("/{activity_id}/equipment", response_model=ActivityResponse)
async def update_activity_equipment(
    activity_id: int,
    update: ActivityUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update the equipment for an activity."""
    result = await db.execute(
        select(Activity).where(
            Activity.id == activity_id, Activity.user_id == user.id
        )
    )
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if update.gear_id:
        # Verify equipment exists and belongs to user
        eq_result = await db.execute(
            select(Equipment).where(
                Equipment.id == update.gear_id, Equipment.user_id == user.id
            )
        )
        equipment = eq_result.scalar_one_or_none()

        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")

        # Update on Strava
        strava = StravaService(user.access_token)
        try:
            await strava.update_activity(
                activity.strava_activity_id, gear_id=equipment.strava_gear_id
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to update Strava: {str(e)}"
            )

        activity.gear_id = equipment.id
        activity.strava_gear_id = equipment.strava_gear_id
    else:
        # Remove equipment
        strava = StravaService(user.access_token)
        try:
            await strava.update_activity(activity.strava_activity_id, gear_id="none")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to update Strava: {str(e)}"
            )

        activity.gear_id = None
        activity.strava_gear_id = None

    await db.commit()
    await db.refresh(activity)

    return ActivityResponse.model_validate(activity)


@router.post("/sync")
async def sync_activities(
    days: int = Query(30, le=365),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sync activities from Strava."""
    strava = StravaService(user.access_token)

    # Get equipment mapping
    eq_result = await db.execute(
        select(Equipment).where(Equipment.user_id == user.id)
    )
    equipment_map = {eq.strava_gear_id: eq for eq in eq_result.scalars().all()}

    # Calculate date range
    after = datetime.utcnow() - timedelta(days=days) if days else None

    synced_count = 0
    created_count = 0
    updated_count = 0
    page = 1

    while True:
        try:
            activities = await strava.get_athlete_activities(
                after=after, page=page, per_page=50
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch from Strava: {str(e)}"
            )

        if not activities:
            break

        for activity_data in activities:
            strava_id = activity_data["id"]

            # Check if activity exists
            result = await db.execute(
                select(Activity).where(
                    Activity.strava_activity_id == strava_id,
                    Activity.user_id == user.id,
                )
            )
            existing = result.scalar_one_or_none()

            # Map gear
            strava_gear_id = activity_data.get("gear_id")
            gear_id = None
            if strava_gear_id and strava_gear_id in equipment_map:
                gear_id = equipment_map[strava_gear_id].id

            if existing:
                # Update existing activity
                existing.name = activity_data.get("name", existing.name)
                existing.activity_type = activity_data.get("type", existing.activity_type)
                existing.sport_type = activity_data.get("sport_type")
                existing.distance = activity_data.get("distance", 0)
                existing.moving_time = activity_data.get("moving_time", 0)
                existing.elapsed_time = activity_data.get("elapsed_time", 0)
                existing.total_elevation_gain = activity_data.get("total_elevation_gain")
                existing.average_speed = activity_data.get("average_speed")
                existing.max_speed = activity_data.get("max_speed")
                existing.trainer = activity_data.get("trainer", False)
                existing.commute = activity_data.get("commute", False)
                existing.manual = activity_data.get("manual", False)
                existing.private = activity_data.get("private", False)
                existing.external_id = activity_data.get("external_id")
                existing.device_name = activity_data.get("device_name")
                existing.gear_id = gear_id
                existing.strava_gear_id = strava_gear_id
                existing.synced_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new activity
                start_date_str = activity_data.get("start_date")
                start_date = (
                    datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                    if start_date_str
                    else datetime.utcnow()
                )

                new_activity = Activity(
                    strava_activity_id=strava_id,
                    user_id=user.id,
                    name=activity_data.get("name", "Untitled"),
                    activity_type=activity_data.get("type", "Unknown"),
                    sport_type=activity_data.get("sport_type"),
                    start_date=start_date,
                    distance=activity_data.get("distance", 0),
                    moving_time=activity_data.get("moving_time", 0),
                    elapsed_time=activity_data.get("elapsed_time", 0),
                    total_elevation_gain=activity_data.get("total_elevation_gain"),
                    average_speed=activity_data.get("average_speed"),
                    max_speed=activity_data.get("max_speed"),
                    trainer=activity_data.get("trainer", False),
                    commute=activity_data.get("commute", False),
                    manual=activity_data.get("manual", False),
                    private=activity_data.get("private", False),
                    external_id=activity_data.get("external_id"),
                    device_name=activity_data.get("device_name"),
                    gear_id=gear_id,
                    strava_gear_id=strava_gear_id,
                )
                db.add(new_activity)
                created_count += 1

            synced_count += 1

        await db.commit()
        page += 1

        # Stop if we got less than a full page
        if len(activities) < 50:
            break

    return {
        "message": "Sync completed",
        "synced": synced_count,
        "created": created_count,
        "updated": updated_count,
    }


@router.post("/bulk-update")
async def bulk_update_equipment(
    update: ActivityBulkUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update equipment for multiple activities at once."""
    # Verify equipment exists
    eq_result = await db.execute(
        select(Equipment).where(
            Equipment.id == update.gear_id, Equipment.user_id == user.id
        )
    )
    equipment = eq_result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    # Get activities
    result = await db.execute(
        select(Activity).where(
            Activity.id.in_(update.activity_ids), Activity.user_id == user.id
        )
    )
    activities = result.scalars().all()

    if not activities:
        raise HTTPException(status_code=404, detail="No activities found")

    strava = StravaService(user.access_token)
    updated_count = 0
    errors = []

    for activity in activities:
        try:
            await strava.update_activity(
                activity.strava_activity_id, gear_id=equipment.strava_gear_id
            )
            activity.gear_id = equipment.id
            activity.strava_gear_id = equipment.strava_gear_id
            updated_count += 1
        except Exception as e:
            errors.append({"activity_id": activity.id, "error": str(e)})

    await db.commit()

    return {
        "message": "Bulk update completed",
        "updated": updated_count,
        "errors": errors,
    }


async def run_backfill(user_id: int, access_token: str, refresh_token: str):
    """Background task to backfill all historical activities."""
    global backfill_status

    backfill_status[user_id] = {
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "pages_processed": 0,
        "activities_found": 0,
        "created": 0,
        "updated": 0,
        "errors": [],
        "completed_at": None,
    }

    current_access_token = access_token
    current_refresh_token = refresh_token

    async def refresh_strava_token():
        """Refresh the Strava token and update in database."""
        nonlocal current_access_token, current_refresh_token
        try:
            token_data = await StravaService.refresh_access_token(current_refresh_token)
            current_access_token = token_data.get("access_token")
            current_refresh_token = token_data.get("refresh_token")
            # Update in database
            async with async_session() as token_db:
                result = await token_db.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                if user:
                    user.access_token = current_access_token
                    user.refresh_token = current_refresh_token
                    user.token_expires_at = datetime.fromtimestamp(token_data.get("expires_at", 0))
                    await token_db.commit()
            return True
        except Exception as e:
            backfill_status[user_id]["errors"].append(f"Token refresh failed: {str(e)}")
            return False

    strava = StravaService(current_access_token)

    try:
        async with async_session() as db:
            # Get equipment mapping
            eq_result = await db.execute(
                select(Equipment).where(Equipment.user_id == user_id)
            )
            equipment_map = {eq.strava_gear_id: eq for eq in eq_result.scalars().all()}

            # Find oldest activity to continue from where we left off
            oldest_result = await db.execute(
                select(Activity.start_date)
                .where(Activity.user_id == user_id)
                .order_by(Activity.start_date.asc())
                .limit(1)
            )
            oldest_date = oldest_result.scalar_one_or_none()

            # Use before parameter to only fetch activities older than our oldest
            before_date = oldest_date if oldest_date else None
            if before_date:
                backfill_status[user_id]["message"] = f"Fetching activities before {before_date.strftime('%Y-%m-%d')}"

            page = 1
            total_created = 0
            total_updated = 0

            while True:
                try:
                    # Fetch activities older than our oldest stored activity
                    activities = await strava.get_athlete_activities(
                        before=before_date, page=page, per_page=100
                    )
                except Exception as e:
                    error_msg = f"Page {page}: [{type(e).__name__}] {str(e)}"

                    # If rate limited, wait and retry
                    if "429" in str(e) or "rate" in str(e).lower():
                        backfill_status[user_id]["status"] = "rate_limited"
                        backfill_status[user_id]["errors"].append(f"Rate limited at page {page}, waiting 15 minutes...")
                        await asyncio.sleep(900)  # Wait 15 minutes
                        backfill_status[user_id]["status"] = "running"
                        continue

                    # If auth error, try to refresh token
                    if "401" in str(e) or "unauthorized" in str(e).lower():
                        backfill_status[user_id]["errors"].append(f"Token expired at page {page}, attempting refresh...")
                        if await refresh_strava_token():
                            strava = StravaService(current_access_token)
                            continue  # Retry the same page with new token
                        else:
                            backfill_status[user_id]["status"] = "error"
                            backfill_status[user_id]["errors"].append("Token refresh failed. Please reconnect to Strava.")
                            return

                    # Other error - log and stop
                    backfill_status[user_id]["errors"].append(error_msg)
                    break

                if not activities:
                    break

                for activity_data in activities:
                    strava_id = activity_data["id"]

                    # Check if activity exists
                    result = await db.execute(
                        select(Activity).where(
                            Activity.strava_activity_id == strava_id,
                            Activity.user_id == user_id,
                        )
                    )
                    existing = result.scalar_one_or_none()

                    # Map gear
                    strava_gear_id = activity_data.get("gear_id")
                    gear_id = None
                    if strava_gear_id and strava_gear_id in equipment_map:
                        gear_id = equipment_map[strava_gear_id].id

                    if existing:
                        # Update existing
                        existing.name = activity_data.get("name", existing.name)
                        existing.activity_type = activity_data.get("type", existing.activity_type)
                        existing.sport_type = activity_data.get("sport_type")
                        existing.distance = activity_data.get("distance", 0)
                        existing.moving_time = activity_data.get("moving_time", 0)
                        existing.elapsed_time = activity_data.get("elapsed_time", 0)
                        existing.total_elevation_gain = activity_data.get("total_elevation_gain")
                        existing.average_speed = activity_data.get("average_speed")
                        existing.max_speed = activity_data.get("max_speed")
                        existing.trainer = activity_data.get("trainer", False)
                        existing.commute = activity_data.get("commute", False)
                        existing.manual = activity_data.get("manual", False)
                        existing.private = activity_data.get("private", False)
                        existing.external_id = activity_data.get("external_id")
                        existing.device_name = activity_data.get("device_name")
                        existing.gear_id = gear_id
                        existing.strava_gear_id = strava_gear_id
                        existing.synced_at = datetime.utcnow()
                        total_updated += 1
                    else:
                        # Create new
                        start_date_str = activity_data.get("start_date")
                        start_date = (
                            datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                            if start_date_str
                            else datetime.utcnow()
                        )

                        new_activity = Activity(
                            strava_activity_id=strava_id,
                            user_id=user_id,
                            name=activity_data.get("name", "Untitled"),
                            activity_type=activity_data.get("type", "Unknown"),
                            sport_type=activity_data.get("sport_type"),
                            start_date=start_date,
                            distance=activity_data.get("distance", 0),
                            moving_time=activity_data.get("moving_time", 0),
                            elapsed_time=activity_data.get("elapsed_time", 0),
                            total_elevation_gain=activity_data.get("total_elevation_gain"),
                            average_speed=activity_data.get("average_speed"),
                            max_speed=activity_data.get("max_speed"),
                            trainer=activity_data.get("trainer", False),
                            commute=activity_data.get("commute", False),
                            manual=activity_data.get("manual", False),
                            private=activity_data.get("private", False),
                            external_id=activity_data.get("external_id"),
                            device_name=activity_data.get("device_name"),
                            gear_id=gear_id,
                            strava_gear_id=strava_gear_id,
                        )
                        db.add(new_activity)
                        total_created += 1

                await db.commit()

                # Update status
                backfill_status[user_id]["pages_processed"] = page
                backfill_status[user_id]["activities_found"] += len(activities)
                backfill_status[user_id]["created"] = total_created
                backfill_status[user_id]["updated"] = total_updated

                page += 1

                # Respect rate limits - small delay between pages
                await asyncio.sleep(0.5)

                # Stop if we got less than a full page
                if len(activities) < 100:
                    break

            backfill_status[user_id]["status"] = "completed"
            backfill_status[user_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        backfill_status[user_id]["status"] = "error"
        backfill_status[user_id]["errors"].append(str(e))


@router.post("/backfill")
async def start_backfill(
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    """Start a background task to backfill all historical activities from Strava."""
    # Check if already running
    if user.id in backfill_status and backfill_status[user.id]["status"] == "running":
        raise HTTPException(
            status_code=409,
            detail="Backfill already in progress"
        )

    # Start background task
    background_tasks.add_task(run_backfill, user.id, user.access_token, user.refresh_token)

    return {
        "message": "Backfill started",
        "status_url": "/api/activities/backfill/status"
    }


@router.get("/backfill/status")
async def get_backfill_status(
    user: User = Depends(get_current_user),
):
    """Get the current status of the backfill process."""
    if user.id not in backfill_status:
        return {
            "status": "not_started",
            "message": "No backfill has been started"
        }

    return backfill_status[user.id]
