# Arq Job Queue Integration Plan

## Overview
Replace FastAPI's in-memory `BackgroundTasks` with Arq (async Redis queue) for persistent, reliable background job processing.

## Current State
- Two background jobs using `BackgroundTasks`: activity backfill and rule application
- In-memory status tracking via global dicts (lost on restart)
- No Redis in stack currently

## New Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FastAPI    │────▶│    Redis    │◀────│  Arq Worker │
│   (API)     │     │   (Queue)   │     │  (Process)  │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Files to Create

### 1. `/backend/app/jobs/__init__.py`
Export job functions and worker settings.

### 2. `/backend/app/jobs/worker.py`
Arq worker configuration with Redis settings, startup/shutdown hooks.

### 3. `/backend/app/jobs/tasks.py`
Job functions extracted from routers:
- `backfill_activities()` - from activities.py:373-559
- `apply_rule()` - from rules.py:412-594

### 4. `/backend/app/jobs/pool.py`
Arq Redis connection pool manager for enqueueing jobs from API.

### 5. `/backend/app/jobs/context.py`
`JobContext` class for token refresh and error handling within jobs.

### 6. `/backend/docker-compose.yml`
Services: redis, api, worker (all sharing same DB).

## Files to Modify

### 1. `/backend/requirements.txt`
Add: `arq>=0.25.0`, `redis>=5.0.0`

### 2. `/backend/app/config.py`
Add Redis settings: `redis_host`, `redis_port`, `redis_db`, `redis_password`

### 3. `/backend/app/main.py`
Add Arq pool initialization/cleanup in lifespan.

### 4. `/backend/app/routers/activities.py`
- Remove: `backfill_status` dict, `run_backfill()` function
- Update `start_backfill()`: enqueue Arq job instead of BackgroundTasks
- Update `get_backfill_status()`: query Arq job result

### 5. `/backend/app/routers/rules.py`
- Remove: `rule_apply_status` dict, `run_rule_apply()` function
- Update `apply_rule()`: enqueue Arq job
- Update `get_apply_status()`: query Arq job result

## Frontend Changes
The existing frontend jobs store and JobsIndicator should continue working since the API contract remains the same - just need to ensure the response format matches.

## Running Locally

```bash
# Terminal 1: Start Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2: Start API
cd backend && uvicorn app.main:app --reload

# Terminal 3: Start Worker
cd backend && arq app.jobs.worker.WorkerSettings
```

## Verification

1. Start Redis, API, and worker processes
2. Trigger activity backfill via UI or API
3. Verify job appears in Jobs indicator
4. Restart API server mid-job
5. Verify job continues and status is still queryable
6. Test rule application with same flow
7. Verify rate limiting waits work correctly
