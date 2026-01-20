# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

**Backend (FastAPI):**
```bash
cd backend
source venv/bin/activate  # or: python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (Vue 3 + Vite):**
```bash
cd frontend
npm install
npm run dev  # Runs on port 5173
```

**Environment Files:**
- Backend: `backend/.env` - requires `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`
- Frontend: `frontend/.env` - set `VITE_API_URL=http://localhost:8000`

## Architecture Overview

This is a Strava Equipment Manager that connects to the Strava API to manage equipment assignments on activities via configurable rules.

### Data Flow

```
Vue 3 SPA (frontend/)
    ↓ Axios HTTP calls
FastAPI (backend/app/)
    ↓ SQLAlchemy async
SQLite (backend/strava_equipment.db)
    ↓ httpx (when syncing/updating)
Strava API (OAuth + REST)
```

### Backend Structure (`backend/app/`)

- **main.py** - FastAPI app with CORS config and lifespan hooks
- **config.py** - Pydantic settings loaded from `.env`
- **database.py** - Async SQLAlchemy engine and session factory
- **models/** - ORM models: User, Activity, Equipment, Rule, RuleCondition
- **routers/** - API endpoints grouped by resource (auth, activities, equipment, rules)
- **services/** - Business logic:
  - `strava.py` - Strava API client with OAuth token refresh
  - `rule_engine.py` - Rule condition evaluation (supports regex, contains, numeric comparisons, AND/OR logic)
- **schemas/** - Pydantic request/response models

### Frontend Structure (`frontend/src/`)

- **api/client.js** - Axios instance with all API methods
- **stores/** - Pinia stores for auth, activities, equipment, rules, jobs
- **views/** - Page components (Home, Activities, Equipment, Rules, etc.)
- **data/** - Mock data for offline development (`VITE_USE_MOCK_DATA=true`)

### Key Patterns

1. **Async everywhere** - All backend DB/HTTP operations use async/await
2. **Background jobs** - Long operations (backfill, rule apply) run as background tasks with in-memory status tracking. Status endpoints allow polling.
3. **Rule Engine** - Rules have conditions evaluated by `RuleEngine.evaluate_rule()`. Supports 15+ operators including regex. Preview before applying.
4. **Token refresh** - Strava tokens auto-refresh on 401 errors

### Database Models

- **users** - Strava athlete info + OAuth tokens
- **equipment** - Bikes/shoes with usage stats (linked to Strava gear_id)
- **activities** - Synced from Strava with local equipment references
- **rules** + **rule_conditions** - User-defined rules for automatic equipment assignment

## API Endpoints

All endpoints prefixed with `/api`. Key endpoints:

- `GET/POST /auth/login|callback|status|logout` - OAuth flow
- `GET /activities` - List with filters (search, type, equipment, date range)
- `POST /activities/sync?days=30` - Sync recent activities from Strava
- `POST /activities/backfill` - Sync all historical activities (background)
- `POST /activities/bulk-update` - Batch equipment update
- `GET /equipment/stats` - Equipment with usage statistics
- `POST /rules/{id}/preview` - Show activities matching rule
- `POST /rules/{id}/apply` - Apply rule to activities (background)

## Plans

Implementation plans are stored in `plans/`:
- `original-implementation-plan.md` - Initial app design
- `arq-integration-plan.md` - Planned migration to Arq job queue for persistent background jobs
