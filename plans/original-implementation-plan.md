# Strava Equipment Manager - Implementation Plan

## Overview
A web application that connects to Strava, imports activities, and allows automatic reassignment of equipment based on configurable rules.

**Tech Stack:**
- Backend: Python 3.11+ with FastAPI
- Frontend: Vue 3 with Vite
- Database: SQLite with SQLAlchemy
- Auth: Strava OAuth 2.0
- Deployment: Local only (localhost)

---

## Phase 1: Strava API Setup (Prerequisites)

### Register a Strava API Application
1. Go to https://www.strava.com/settings/api
2. Create a new application with:
   - **Application Name:** "Equipment Manager" (or your choice)
   - **Category:** "Training/Fitness"
   - **Website:** `http://localhost:5173`
   - **Authorization Callback Domain:** `localhost`
3. Note your **Client ID** and **Client Secret**

### Required OAuth Scopes
- `read` - Read public profile
- `activity:read_all` - Read all activities (including private)
- `activity:write` - Update activities (to change equipment)
- `profile:read_all` - Read gear/equipment list

---

## Phase 2: Project Structure

```
strava-equipment-manager/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings/environment config
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── activity.py      # Activity model
│   │   │   ├── equipment.py     # Equipment model
│   │   │   ├── rule.py          # Rule model
│   │   │   └── user.py          # User/token storage
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # OAuth endpoints
│   │   │   ├── activities.py    # Activity CRUD
│   │   │   ├── equipment.py     # Equipment endpoints
│   │   │   └── rules.py         # Rule management
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── strava.py        # Strava API client
│   │   │   └── rule_engine.py   # Rule matching logic
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── *.py             # Pydantic schemas
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── stores/
│   │   │   ├── auth.js          # Pinia auth store
│   │   │   ├── activities.js
│   │   │   └── rules.js
│   │   ├── views/
│   │   │   ├── HomeView.vue
│   │   │   ├── ActivitiesView.vue
│   │   │   ├── EquipmentView.vue
│   │   │   ├── RulesView.vue
│   │   │   └── CallbackView.vue
│   │   ├── components/
│   │   │   ├── ActivityList.vue
│   │   │   ├── ActivityFilters.vue
│   │   │   ├── RuleEditor.vue
│   │   │   ├── RulePreview.vue
│   │   │   └── StatsChart.vue
│   │   └── api/
│   │       └── client.js        # Axios API client
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## Phase 3: Database Schema

### Tables

**users**
- id (PK)
- strava_athlete_id (unique)
- access_token (encrypted)
- refresh_token (encrypted)
- token_expires_at
- created_at, updated_at

**equipment**
- id (PK)
- strava_gear_id (unique)
- user_id (FK)
- name
- equipment_type (bike, shoes)
- brand_name, model_name
- distance (meters)
- is_primary
- is_retired
- synced_at

**activities**
- id (PK)
- strava_activity_id (unique)
- user_id (FK)
- name
- activity_type (Ride, Run, VirtualRide, etc.)
- sport_type
- start_date
- distance, moving_time, elapsed_time
- trainer (boolean)
- gear_id (current equipment)
- external_id (for detecting Zwift, etc.)
- device_name
- synced_at

**rules**
- id (PK)
- user_id (FK)
- name
- priority (for rule ordering)
- target_gear_id (equipment to assign)
- is_active
- created_at, updated_at

**rule_conditions**
- id (PK)
- rule_id (FK)
- field (activity_type, name, trainer, device_name, etc.)
- operator (equals, contains, starts_with, regex, etc.)
- value
- logic (AND/OR with other conditions)

---

## Phase 4: Backend Implementation

### 4.1 Core Setup
- FastAPI application with CORS for Vue frontend
- SQLAlchemy async engine with SQLite
- Pydantic settings for environment variables
- Token encryption using cryptography library

### 4.2 Strava OAuth Flow
1. `/auth/login` - Redirect to Strava authorization
2. `/auth/callback` - Handle OAuth callback, exchange code for tokens
3. `/auth/refresh` - Auto-refresh expired tokens
4. `/auth/logout` - Clear local tokens

### 4.3 Strava API Integration
- `GET /athlete` - Get athlete profile
- `GET /athlete/activities` - Fetch activities (paginated)
- `GET /gear/{id}` - Get equipment details
- `PUT /activities/{id}` - Update activity (change gear)

### 4.4 API Endpoints

**Auth:**
- `GET /api/auth/login` - Start OAuth
- `GET /api/auth/callback` - OAuth callback
- `GET /api/auth/status` - Check auth status
- `POST /api/auth/logout` - Logout

**Activities:**
- `GET /api/activities` - List with filters
- `POST /api/activities/sync` - Sync from Strava
- `GET /api/activities/{id}` - Get single activity
- `PATCH /api/activities/{id}/equipment` - Update equipment

**Equipment:**
- `GET /api/equipment` - List all equipment
- `POST /api/equipment/sync` - Sync from Strava
- `GET /api/equipment/stats` - Usage statistics

**Rules:**
- `GET /api/rules` - List all rules
- `POST /api/rules` - Create rule
- `PUT /api/rules/{id}` - Update rule
- `DELETE /api/rules/{id}` - Delete rule
- `POST /api/rules/preview` - Preview matching activities
- `POST /api/rules/apply` - Apply rules to activities

### 4.5 Rule Engine
The rule engine evaluates activities against rules:

```python
# Simple rule: name contains "Zwift"
{
    "name": "Zwift rides",
    "target_gear_id": "b12345",
    "conditions": [
        {"field": "name", "operator": "contains", "value": "Zwift"}
    ]
}

# Advanced rule: Indoor trainer ride on weekday morning
{
    "name": "Morning trainer rides",
    "target_gear_id": "b12345",
    "conditions": [
        {"field": "trainer", "operator": "equals", "value": true},
        {"field": "activity_type", "operator": "equals", "value": "Ride"},
        {"field": "start_hour", "operator": "less_than", "value": 10}
    ]
}
```

---

## Phase 5: Frontend Implementation

### 5.1 Setup
- Vue 3 with Composition API
- Vue Router for navigation
- Pinia for state management
- Axios for API calls
- Chart.js or ApexCharts for statistics
- Tailwind CSS for styling

### 5.2 Views

**Home/Dashboard**
- Auth status and connect button
- Quick stats (total activities, equipment count)
- Recent activities preview

**Activities**
- Paginated activity list
- Filters: date range, activity type, equipment, trainer flag
- Bulk select for equipment changes
- Rule match indicator

**Equipment**
- List all bikes and shoes
- Usage stats per equipment (distance, time, activity count)
- Charts showing usage over time
- Set as default equipment

**Rules**
- Rule list with drag-to-reorder priority
- Rule editor modal
- Condition builder UI
- Preview: show activities that would match
- Apply: execute rules and update Strava

### 5.3 Key Components

**RuleEditor**
- Add/edit rule name
- Select target equipment
- Condition builder with:
  - Field selector (name, type, trainer, device, time)
  - Operator selector (based on field type)
  - Value input (text, dropdown, number)
  - AND/OR logic toggle
  - Add/remove conditions

**RulePreview**
- Table of activities that match the rule
- Current equipment vs proposed equipment
- Select/deselect individual activities
- Apply button with confirmation

---

## Phase 6: Implementation Order

### Step 0: Visual Prototype (FIRST)
Build a static Vue prototype with mock data to validate UI design before backend work.

**0.1 - Project Setup**
- Initialize Vue 3 + Vite project
- Add Tailwind CSS for styling
- Set up Vue Router for navigation
- Create basic layout (nav, sidebar, main content)

**0.2 - Mock Data**
Create realistic mock data in JSON files:
- 20-30 sample activities (mix of types, equipment)
- 5-6 pieces of equipment (bikes, shoes)
- 3-4 sample rules

**0.3 - Prototype Views**
Build all views with static mock data:
1. **Dashboard** - Auth status, quick stats, recent activities
2. **Activities** - Table with filters (type, date, equipment, trainer)
3. **Equipment** - Cards with usage stats, charts
4. **Rules** - Rule list, editor modal, preview panel

**0.4 - Review Checkpoint**
- Capture screenshots of all views
- User reviews in browser
- Gather feedback and iterate on design
- **STOP HERE** until design is approved

---

### Step 1: Backend Foundation (after prototype approval)
1. Initialize FastAPI project with dependencies
2. Set up SQLAlchemy models and database
3. Create config/settings management
4. Implement Strava OAuth flow

### Step 2: Strava Integration
1. Build Strava API client service
2. Implement activity sync endpoint
3. Implement equipment sync endpoint
4. Add token refresh logic

### Step 3: Core API
1. Activities CRUD endpoints
2. Equipment endpoints with stats
3. Basic rule storage (CRUD)

### Step 4: Rule Engine
1. Rule evaluation logic
2. Preview endpoint (dry run)
3. Apply endpoint (update Strava)

### Step 5: Connect Frontend to Backend
1. Replace mock data with API calls
2. Implement auth flow in Vue
3. Add loading states and error handling
4. Wire up all CRUD operations

### Step 6: Polish
1. Responsive design refinements
2. Error handling edge cases
3. README and setup documentation

---

## Verification Plan

### Development Workflow
- **Playwright screenshots**: After building each view/component, I'll capture screenshots using the webapp-testing skill to verify layout and functionality
- **Manual review**: You review in browser for final approval at key milestones
- **API testing**: Use httpx/curl to verify backend endpoints return expected data

### Backend Testing
1. Start FastAPI server: `uvicorn app.main:app --reload --port 8000`
2. Test endpoints with curl/httpx:
   - `GET /api/auth/status` - Check auth state
   - `GET /api/activities` - Verify activity list returns data
   - `POST /api/rules` - Test rule creation
3. Test OAuth flow by visiting `http://localhost:8000/api/auth/login`

### Frontend Testing (with Playwright)
After each major view is complete:
1. Start Vue dev server: `npm run dev` (runs on port 5173)
2. Use webapp-testing skill to capture screenshots:
   - Home page / login state
   - Activities list view
   - Equipment stats view
   - Rule editor modal
   - Rule preview results
3. Verify responsive layout at different viewport sizes
4. You do final review in browser before moving to next phase

### Milestone Checkpoints
- **Checkpoint 1**: Backend OAuth + basic sync working (API test)
- **Checkpoint 2**: Frontend auth flow + activities view (screenshot + your review)
- **Checkpoint 3**: Equipment stats with charts (screenshot + your review)
- **Checkpoint 4**: Rule editor and preview (screenshot + your review)
- **Checkpoint 5**: Full end-to-end flow working (your manual test)

### End-to-End Verification
1. Connect Strava account via OAuth
2. Sync activities and equipment from Strava
3. Create a rule (e.g., "Zwift" → Zwift bike)
4. Preview matches - verify correct activities shown
5. Apply rule
6. Verify on Strava website that equipment changed

---

## Dependencies

### Backend (requirements.txt)
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
httpx>=0.26.0
python-dotenv>=1.0.0
cryptography>=42.0.0
pydantic-settings>=2.1.0
```

### Frontend (package.json)
```
vue: ^3.4
vue-router: ^4.2
pinia: ^2.1
axios: ^1.6
chart.js: ^4.4
tailwindcss: ^3.4
```

---

## Environment Variables

```env
# Backend (.env)
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REDIRECT_URI=http://localhost:8000/api/auth/callback
SECRET_KEY=your_random_secret_key
DATABASE_URL=sqlite+aiosqlite:///./strava_equipment.db
FRONTEND_URL=http://localhost:5173

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```
