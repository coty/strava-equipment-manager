from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.schemas.user import UserResponse, AuthStatus
from app.services.strava import StravaService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# Simple session storage (in production, use proper session management)
_current_user_id: int | None = None


def get_current_user_id() -> int | None:
    return _current_user_id


@router.get("/login")
async def login():
    """Redirect to Strava OAuth authorization page."""
    auth_url = StravaService.get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    code: str = Query(None),
    error: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from Strava."""
    global _current_user_id

    if error:
        return RedirectResponse(
            url=f"{settings.frontend_url}/callback?error={error}"
        )

    if not code:
        return RedirectResponse(
            url=f"{settings.frontend_url}/callback?error=no_code"
        )

    try:
        # Exchange code for tokens
        token_data = await StravaService.exchange_code(code)

        athlete_data = token_data.get("athlete", {})
        athlete_id = athlete_data.get("id")

        if not athlete_id:
            raise HTTPException(status_code=400, detail="Invalid athlete data")

        # Check if user exists
        result = await db.execute(
            select(User).where(User.strava_athlete_id == athlete_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update existing user
            user.access_token = token_data.get("access_token")
            user.refresh_token = token_data.get("refresh_token")
            user.token_expires_at = datetime.fromtimestamp(
                token_data.get("expires_at", 0)
            )
            user.firstname = athlete_data.get("firstname")
            user.lastname = athlete_data.get("lastname")
            user.profile = athlete_data.get("profile")
            user.city = athlete_data.get("city")
            user.state = athlete_data.get("state")
            user.country = athlete_data.get("country")
        else:
            # Create new user
            user = User(
                strava_athlete_id=athlete_id,
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                token_expires_at=datetime.fromtimestamp(
                    token_data.get("expires_at", 0)
                ),
                firstname=athlete_data.get("firstname"),
                lastname=athlete_data.get("lastname"),
                profile=athlete_data.get("profile"),
                city=athlete_data.get("city"),
                state=athlete_data.get("state"),
                country=athlete_data.get("country"),
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)

        _current_user_id = user.id

        return RedirectResponse(url=f"{settings.frontend_url}/callback?success=true")

    except Exception as e:
        return RedirectResponse(
            url=f"{settings.frontend_url}/callback?error={str(e)}"
        )


@router.get("/status", response_model=AuthStatus)
async def get_auth_status(db: AsyncSession = Depends(get_db)):
    """Check current authentication status."""
    global _current_user_id

    if not _current_user_id:
        return AuthStatus(is_authenticated=False)

    result = await db.execute(select(User).where(User.id == _current_user_id))
    user = result.scalar_one_or_none()

    if not user:
        _current_user_id = None
        return AuthStatus(is_authenticated=False)

    # Check if token needs refresh
    if user.is_token_expired() and user.refresh_token:
        try:
            token_data = await StravaService.refresh_access_token(user.refresh_token)
            user.access_token = token_data.get("access_token")
            user.refresh_token = token_data.get("refresh_token")
            user.token_expires_at = datetime.fromtimestamp(
                token_data.get("expires_at", 0)
            )
            await db.commit()
        except Exception:
            # Token refresh failed
            _current_user_id = None
            return AuthStatus(is_authenticated=False)

    return AuthStatus(
        is_authenticated=True,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout():
    """Clear the current session."""
    global _current_user_id
    _current_user_id = None
    return {"message": "Logged out successfully"}


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to get the current authenticated user."""
    global _current_user_id

    if not _current_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(User).where(User.id == _current_user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Refresh token if expired
    if user.is_token_expired() and user.refresh_token:
        try:
            token_data = await StravaService.refresh_access_token(user.refresh_token)
            user.access_token = token_data.get("access_token")
            user.refresh_token = token_data.get("refresh_token")
            user.token_expires_at = datetime.fromtimestamp(
                token_data.get("expires_at", 0)
            )
            await db.commit()
        except Exception:
            raise HTTPException(status_code=401, detail="Token refresh failed")

    return user
