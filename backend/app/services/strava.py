import httpx
from datetime import datetime, timedelta
from typing import Any
from app.config import get_settings

settings = get_settings()

# Timeout for Strava API requests (seconds)
API_TIMEOUT = 30.0


class StravaService:
    def __init__(self, access_token: str | None = None):
        self.access_token = access_token
        self.base_url = settings.strava_api_base

    def _get_headers(self) -> dict:
        if not self.access_token:
            raise ValueError("Access token is required")
        return {"Authorization": f"Bearer {self.access_token}"}

    @staticmethod
    def get_authorization_url(state: str = "") -> str:
        """Generate the Strava OAuth authorization URL."""
        scopes = "read,activity:read_all,activity:write,profile:read_all"
        return (
            f"{settings.strava_auth_url}"
            f"?client_id={settings.strava_client_id}"
            f"&redirect_uri={settings.strava_redirect_uri}"
            f"&response_type=code"
            f"&scope={scopes}"
            f"&state={state}"
        )

    @staticmethod
    async def exchange_code(code: str) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(
                settings.strava_token_url,
                data={
                    "client_id": settings.strava_client_id,
                    "client_secret": settings.strava_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
        """Refresh the access token using the refresh token."""
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(
                settings.strava_token_url,
                data={
                    "client_id": settings.strava_client_id,
                    "client_secret": settings.strava_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_athlete(self) -> dict[str, Any]:
        """Get the authenticated athlete's profile."""
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/athlete",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_athlete_activities(
        self,
        before: datetime | None = None,
        after: datetime | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> list[dict[str, Any]]:
        """Get the authenticated athlete's activities."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}

        if before:
            params["before"] = int(before.timestamp())
        if after:
            params["after"] = int(after.timestamp())

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/athlete/activities",
                headers=self._get_headers(),
                params=params,
            )
            if response.status_code != 200:
                error_detail = response.text[:500] if response.text else "No response body"
                raise Exception(f"Strava API error {response.status_code}: {error_detail}")
            return response.json()

    async def get_activity(self, activity_id: int) -> dict[str, Any]:
        """Get a specific activity by ID."""
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/activities/{activity_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def update_activity(
        self, activity_id: int, gear_id: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """Update an activity (e.g., change gear)."""
        data = {}
        if gear_id is not None:
            data["gear_id"] = gear_id
        data.update(kwargs)

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.put(
                f"{self.base_url}/activities/{activity_id}",
                headers=self._get_headers(),
                json=data,
            )
            response.raise_for_status()
            return response.json()

    async def get_gear(self, gear_id: str) -> dict[str, Any]:
        """Get gear details by ID."""
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(
                f"{self.base_url}/gear/{gear_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_all_gear(self) -> list[dict[str, Any]]:
        """Get all gear for the authenticated athlete."""
        athlete = await self.get_athlete()
        gear_list = []

        # Get bikes
        for bike in athlete.get("bikes", []):
            gear_data = await self.get_gear(bike["id"])
            gear_data["equipment_type"] = "bike"
            gear_list.append(gear_data)

        # Get shoes
        for shoe in athlete.get("shoes", []):
            gear_data = await self.get_gear(shoe["id"])
            gear_data["equipment_type"] = "shoes"
            gear_list.append(gear_data)

        return gear_list
