import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db, async_session
from app.models.user import User
from app.models.rule import Rule, RuleCondition
from app.models.equipment import Equipment
from app.models.activity import Activity
from app.schemas.rule import (
    RuleResponse,
    RuleCreate,
    RuleUpdate,
    RulePreviewResponse,
    RulePreviewActivity,
)
from app.routers.auth import get_current_user
from app.services.rule_engine import RuleEngine
from app.services.strava import StravaService

router = APIRouter(prefix="/rules", tags=["rules"])

# In-memory status tracking for rule application jobs
rule_apply_status: dict[str, dict] = {}


@router.get("", response_model=list[RuleResponse])
async def get_rules(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all rules for the current user."""
    result = await db.execute(
        select(Rule)
        .where(Rule.user_id == user.id)
        .options(selectinload(Rule.conditions))
        .order_by(Rule.priority)
    )
    rules = result.scalars().all()

    # Build equipment map for rule engine lookups
    all_equipment_result = await db.execute(
        select(Equipment).where(Equipment.user_id == user.id)
    )
    all_equipment = all_equipment_result.scalars().all()
    equipment_map = {eq.id: eq.name for eq in all_equipment}
    RuleEngine.set_equipment_map(equipment_map)

    # Get equipment names and matching counts
    response = []
    for rule in rules:
        rule_dict = {
            "id": rule.id,
            "user_id": rule.user_id,
            "name": rule.name,
            "priority": rule.priority,
            "target_gear_id": rule.target_gear_id,
            "is_active": rule.is_active,
            "conditions": [
                {
                    "id": c.id,
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                    "logic": c.logic,
                }
                for c in rule.conditions
            ],
            "created_at": rule.created_at,
            "updated_at": rule.updated_at,
        }

        # Get equipment name
        eq_result = await db.execute(
            select(Equipment).where(Equipment.id == rule.target_gear_id)
        )
        equipment = eq_result.scalar_one_or_none()
        rule_dict["target_gear_name"] = equipment.name if equipment else None

        # Get matching count
        activities_result = await db.execute(
            select(Activity).where(Activity.user_id == user.id)
        )
        activities = activities_result.scalars().all()
        matching = RuleEngine.find_matching_activities(activities, rule)
        rule_dict["matching_count"] = len(matching)

        response.append(RuleResponse(**rule_dict))

    return response


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific rule by ID."""
    result = await db.execute(
        select(Rule)
        .where(Rule.id == rule_id, Rule.user_id == user.id)
        .options(selectinload(Rule.conditions))
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Get equipment name and build equipment map
    all_equipment_result = await db.execute(
        select(Equipment).where(Equipment.user_id == user.id)
    )
    all_equipment = all_equipment_result.scalars().all()
    equipment_map = {eq.id: eq.name for eq in all_equipment}
    RuleEngine.set_equipment_map(equipment_map)

    equipment = next((eq for eq in all_equipment if eq.id == rule.target_gear_id), None)

    # Get matching count
    activities_result = await db.execute(
        select(Activity).where(Activity.user_id == user.id)
    )
    activities = activities_result.scalars().all()
    matching = RuleEngine.find_matching_activities(activities, rule)

    return RuleResponse(
        id=rule.id,
        user_id=rule.user_id,
        name=rule.name,
        priority=rule.priority,
        target_gear_id=rule.target_gear_id,
        target_gear_name=equipment.name if equipment else None,
        is_active=rule.is_active,
        conditions=[
            {
                "id": c.id,
                "field": c.field,
                "operator": c.operator,
                "value": c.value,
                "logic": c.logic,
            }
            for c in rule.conditions
        ],
        matching_count=len(matching),
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.post("", response_model=RuleResponse)
async def create_rule(
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new rule."""
    # Verify equipment exists
    eq_result = await db.execute(
        select(Equipment).where(
            Equipment.id == rule_data.target_gear_id, Equipment.user_id == user.id
        )
    )
    equipment = eq_result.scalar_one_or_none()

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    # Create rule
    rule = Rule(
        user_id=user.id,
        name=rule_data.name,
        priority=rule_data.priority,
        target_gear_id=rule_data.target_gear_id,
        is_active=rule_data.is_active,
    )
    db.add(rule)
    await db.flush()

    # Create conditions
    for condition_data in rule_data.conditions:
        condition = RuleCondition(
            rule_id=rule.id,
            field=condition_data.field,
            operator=condition_data.operator,
            value=condition_data.value,
            logic=condition_data.logic,
        )
        db.add(condition)

    await db.commit()
    await db.refresh(rule)

    # Load conditions
    result = await db.execute(
        select(Rule)
        .where(Rule.id == rule.id)
        .options(selectinload(Rule.conditions))
    )
    rule = result.scalar_one()

    return RuleResponse(
        id=rule.id,
        user_id=rule.user_id,
        name=rule.name,
        priority=rule.priority,
        target_gear_id=rule.target_gear_id,
        target_gear_name=equipment.name,
        is_active=rule.is_active,
        conditions=[
            {
                "id": c.id,
                "field": c.field,
                "operator": c.operator,
                "value": c.value,
                "logic": c.logic,
            }
            for c in rule.conditions
        ],
        matching_count=0,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update an existing rule."""
    result = await db.execute(
        select(Rule)
        .where(Rule.id == rule_id, Rule.user_id == user.id)
        .options(selectinload(Rule.conditions))
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Update fields
    if rule_data.name is not None:
        rule.name = rule_data.name
    if rule_data.priority is not None:
        rule.priority = rule_data.priority
    if rule_data.is_active is not None:
        rule.is_active = rule_data.is_active

    if rule_data.target_gear_id is not None:
        # Verify equipment exists
        eq_result = await db.execute(
            select(Equipment).where(
                Equipment.id == rule_data.target_gear_id, Equipment.user_id == user.id
            )
        )
        equipment = eq_result.scalar_one_or_none()
        if not equipment:
            raise HTTPException(status_code=404, detail="Equipment not found")
        rule.target_gear_id = rule_data.target_gear_id

    # Update conditions if provided
    if rule_data.conditions is not None:
        # Delete existing conditions
        for condition in rule.conditions:
            await db.delete(condition)

        # Create new conditions
        for condition_data in rule_data.conditions:
            condition = RuleCondition(
                rule_id=rule.id,
                field=condition_data.field,
                operator=condition_data.operator,
                value=condition_data.value,
                logic=condition_data.logic,
            )
            db.add(condition)

    await db.commit()

    # Reload rule with conditions
    result = await db.execute(
        select(Rule)
        .where(Rule.id == rule.id)
        .options(selectinload(Rule.conditions))
    )
    rule = result.scalar_one()

    # Get equipment name
    eq_result = await db.execute(
        select(Equipment).where(Equipment.id == rule.target_gear_id)
    )
    equipment = eq_result.scalar_one_or_none()

    return RuleResponse(
        id=rule.id,
        user_id=rule.user_id,
        name=rule.name,
        priority=rule.priority,
        target_gear_id=rule.target_gear_id,
        target_gear_name=equipment.name if equipment else None,
        is_active=rule.is_active,
        conditions=[
            {
                "id": c.id,
                "field": c.field,
                "operator": c.operator,
                "value": c.value,
                "logic": c.logic,
            }
            for c in rule.conditions
        ],
        matching_count=0,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a rule."""
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id, Rule.user_id == user.id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()

    return {"message": "Rule deleted"}


@router.post("/{rule_id}/preview", response_model=RulePreviewResponse)
async def preview_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Preview which activities match a rule."""
    result = await db.execute(
        select(Rule)
        .where(Rule.id == rule_id, Rule.user_id == user.id)
        .options(selectinload(Rule.conditions))
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Get all equipment and build map for rule engine
    all_equipment_result = await db.execute(
        select(Equipment).where(Equipment.user_id == user.id)
    )
    all_equipment = all_equipment_result.scalars().all()
    equipment_map = {eq.id: eq.name for eq in all_equipment}
    RuleEngine.set_equipment_map(equipment_map)

    target_equipment = next((eq for eq in all_equipment if eq.id == rule.target_gear_id), None)

    # Get all activities
    activities_result = await db.execute(
        select(Activity).where(Activity.user_id == user.id)
    )
    activities = activities_result.scalars().all()

    # Find matching activities
    matching = RuleEngine.find_matching_activities(activities, rule)

    # Build response
    preview_activities = []
    for activity in matching:
        current_gear_name = equipment_map.get(activity.gear_id) if activity.gear_id else None

        preview_activities.append(
            RulePreviewActivity(
                id=activity.id,
                strava_activity_id=activity.strava_activity_id,
                name=activity.name,
                activity_type=activity.activity_type,
                start_date=activity.start_date,
                distance=activity.distance,
                moving_time=activity.moving_time,
                current_gear_id=activity.gear_id,
                current_gear_name=current_gear_name,
                new_gear_id=rule.target_gear_id,
                new_gear_name=target_equipment.name if target_equipment else "Unknown",
            )
        )

    return RulePreviewResponse(
        rule_id=rule.id,
        rule_name=rule.name,
        target_gear_id=rule.target_gear_id,
        target_gear_name=target_equipment.name if target_equipment else "Unknown",
        matching_activities=preview_activities,
        total_count=len(preview_activities),
    )


async def run_rule_apply(
    job_id: str,
    user_id: int,
    rule_id: int,
    activity_ids: list[int] | None,
    access_token: str,
    refresh_token: str,
):
    """Background task to apply a rule to activities."""
    global rule_apply_status

    rule_apply_status[job_id] = {
        "status": "running",
        "rule_id": rule_id,
        "started_at": datetime.utcnow().isoformat(),
        "total": 0,
        "processed": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "completed_at": None,
    }

    current_access_token = access_token
    current_refresh_token = refresh_token

    async def refresh_strava_token():
        """Refresh the Strava token."""
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
            rule_apply_status[job_id]["errors"].append(f"Token refresh failed: {str(e)}")
            return False

    try:
        async with async_session() as db:
            # Load rule with conditions
            result = await db.execute(
                select(Rule)
                .where(Rule.id == rule_id, Rule.user_id == user_id)
                .options(selectinload(Rule.conditions))
            )
            rule = result.scalar_one_or_none()

            if not rule:
                rule_apply_status[job_id]["status"] = "error"
                rule_apply_status[job_id]["errors"].append("Rule not found")
                return

            # Get all equipment and build map for rule engine
            all_equipment_result = await db.execute(
                select(Equipment).where(Equipment.user_id == user_id)
            )
            all_equipment = all_equipment_result.scalars().all()
            equipment_map = {eq.id: eq.name for eq in all_equipment}
            RuleEngine.set_equipment_map(equipment_map)

            target_equipment = next((eq for eq in all_equipment if eq.id == rule.target_gear_id), None)

            if not target_equipment:
                rule_apply_status[job_id]["status"] = "error"
                rule_apply_status[job_id]["errors"].append("Target equipment not found")
                return

            # Get activities to process
            if activity_ids:
                activities_result = await db.execute(
                    select(Activity).where(
                        Activity.id.in_(activity_ids), Activity.user_id == user_id
                    )
                )
            else:
                activities_result = await db.execute(
                    select(Activity).where(Activity.user_id == user_id)
                )

            activities = activities_result.scalars().all()

            # Filter to matching activities
            matching = RuleEngine.find_matching_activities(activities, rule)

            if not matching:
                rule_apply_status[job_id]["status"] = "completed"
                rule_apply_status[job_id]["completed_at"] = datetime.utcnow().isoformat()
                return

            rule_apply_status[job_id]["total"] = len(matching)

            # Update activities on Strava
            strava = StravaService(current_access_token)

            for activity in matching:
                try:
                    await strava.update_activity(
                        activity.strava_activity_id, gear_id=target_equipment.strava_gear_id
                    )
                    activity.gear_id = target_equipment.id
                    activity.strava_gear_id = target_equipment.strava_gear_id
                    rule_apply_status[job_id]["updated"] += 1
                except Exception as e:
                    error_str = str(e)
                    # If auth error, try to refresh token
                    if "401" in error_str or "unauthorized" in error_str.lower():
                        if await refresh_strava_token():
                            strava = StravaService(current_access_token)
                            # Retry this activity
                            try:
                                await strava.update_activity(
                                    activity.strava_activity_id, gear_id=target_equipment.strava_gear_id
                                )
                                activity.gear_id = target_equipment.id
                                activity.strava_gear_id = target_equipment.strava_gear_id
                                rule_apply_status[job_id]["updated"] += 1
                            except Exception as retry_e:
                                rule_apply_status[job_id]["errors"].append({
                                    "activity_id": activity.id,
                                    "name": activity.name,
                                    "error": str(retry_e)
                                })
                        else:
                            rule_apply_status[job_id]["status"] = "error"
                            rule_apply_status[job_id]["errors"].append("Authentication failed")
                            return
                    # If rate limited, wait and retry
                    elif "429" in error_str or "rate" in error_str.lower():
                        rule_apply_status[job_id]["status"] = "rate_limited"
                        await asyncio.sleep(900)  # Wait 15 minutes
                        rule_apply_status[job_id]["status"] = "running"
                        strava = StravaService(current_access_token)
                        # Retry this activity
                        try:
                            await strava.update_activity(
                                activity.strava_activity_id, gear_id=target_equipment.strava_gear_id
                            )
                            activity.gear_id = target_equipment.id
                            activity.strava_gear_id = target_equipment.strava_gear_id
                            rule_apply_status[job_id]["updated"] += 1
                        except Exception as retry_e:
                            rule_apply_status[job_id]["errors"].append({
                                "activity_id": activity.id,
                                "name": activity.name,
                                "error": str(retry_e)
                            })
                    else:
                        rule_apply_status[job_id]["errors"].append({
                            "activity_id": activity.id,
                            "name": activity.name,
                            "error": error_str
                        })

                rule_apply_status[job_id]["processed"] += 1

                # Commit periodically to save progress
                if rule_apply_status[job_id]["processed"] % 10 == 0:
                    await db.commit()

                # Small delay to avoid rate limits
                await asyncio.sleep(0.2)

            await db.commit()

            rule_apply_status[job_id]["status"] = "completed"
            rule_apply_status[job_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        rule_apply_status[job_id]["status"] = "error"
        rule_apply_status[job_id]["errors"].append(str(e))


@router.post("/{rule_id}/apply")
async def apply_rule(
    rule_id: int,
    background_tasks: BackgroundTasks,
    activity_ids: list[int] | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start applying a rule to matching activities (async)."""
    # Verify rule exists
    result = await db.execute(
        select(Rule).where(Rule.id == rule_id, Rule.user_id == user.id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Generate job ID
    job_id = f"rule_{rule_id}_{user.id}_{int(datetime.utcnow().timestamp())}"

    # Check if already running
    for jid, status in rule_apply_status.items():
        if status.get("rule_id") == rule_id and status.get("status") == "running":
            raise HTTPException(
                status_code=409,
                detail="Rule is already being applied"
            )

    # Start background task
    background_tasks.add_task(
        run_rule_apply,
        job_id,
        user.id,
        rule_id,
        activity_ids,
        user.access_token,
        user.refresh_token,
    )

    return {
        "message": "Rule application started",
        "job_id": job_id,
        "status_url": f"/api/rules/{rule_id}/apply/status"
    }


@router.get("/{rule_id}/apply/status")
async def get_apply_status(
    rule_id: int,
    user: User = Depends(get_current_user),
):
    """Get the status of rule application."""
    # Find the latest job for this rule and user
    latest_job = None
    latest_time = None

    for job_id, status in rule_apply_status.items():
        if status.get("rule_id") == rule_id and job_id.endswith(f"_{user.id}_"):
            # Actually check properly
            pass

    # Find matching jobs
    matching_jobs = [
        (jid, status) for jid, status in rule_apply_status.items()
        if status.get("rule_id") == rule_id and f"_{user.id}_" in jid
    ]

    if not matching_jobs:
        return {
            "status": "not_started",
            "message": "No apply job found for this rule"
        }

    # Return the most recent job
    latest_job_id, latest_status = max(matching_jobs, key=lambda x: x[0])
    return {
        "job_id": latest_job_id,
        **latest_status
    }
