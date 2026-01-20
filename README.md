# Strava Equipment Manager

A web application that connects to Strava, imports activities, and allows automatic reassignment of equipment based on configurable rules.

## Features

- **Strava OAuth Integration**: Connect your Strava account securely
- **Activity Sync**: Import activities from Strava with full metadata
- **Equipment Management**: View and manage all your bikes and shoes
- **Rule-Based Assignment**: Create rules to automatically assign equipment based on:
  - Activity name (contains, starts with, regex)
  - Activity type (Ride, Run, VirtualRide, etc.)
  - Trainer/indoor flag
  - Device name (Zwift, TrainerRoad, etc.)
  - And more...
- **Preview & Apply**: Preview which activities match a rule before applying changes
- **Bulk Operations**: Update equipment for multiple activities at once

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: Vue 3 with Vite
- **Database**: SQLite with SQLAlchemy (async)
- **Auth**: Strava OAuth 2.0
- **Styling**: Tailwind CSS

## Prerequisites

1. Python 3.11 or higher
2. Node.js 18 or higher
3. A Strava API application (see Setup)

## Setup

### 1. Create a Strava API Application

1. Go to https://www.strava.com/settings/api
2. Create a new application with:
   - **Application Name**: "Equipment Manager" (or your choice)
   - **Category**: "Training/Fitness"
   - **Website**: `http://localhost:5173`
   - **Authorization Callback Domain**: `localhost`
3. Note your **Client ID** and **Client Secret**

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your Strava credentials
# STRAVA_CLIENT_ID=your_client_id
# STRAVA_CLIENT_SECRET=your_client_secret

# Run the server
uvicorn app.main:app --reload --port 8000
```

The backend will be available at http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file (optional - defaults work for local development)
echo "VITE_API_URL=http://localhost:8000" > .env
echo "VITE_USE_MOCK_DATA=false" >> .env

# Run the development server
npm run dev
```

The frontend will be available at http://localhost:5173

## Usage

### 1. Connect to Strava

1. Open http://localhost:5173 in your browser
2. Click "Connect with Strava" in the sidebar
3. Authorize the application on Strava
4. You'll be redirected back to the app

### 2. Sync Your Data

1. Click "Sync from Strava" on the Equipment page to import your gear
2. Click "Sync from Strava" on the Activities page to import recent activities

### 3. Create Rules

1. Go to the Rules page
2. Click "New Rule"
3. Configure:
   - **Name**: A descriptive name for the rule
   - **Target Equipment**: The equipment to assign when the rule matches
   - **Conditions**: One or more conditions that must match

Example rule for Zwift rides:
- Name: "Zwift Rides"
- Target: Your indoor trainer bike
- Condition: Activity name contains "Zwift"

### 4. Preview and Apply

1. Click the preview icon (eye) on a rule to see matching activities
2. Review the activities that will be updated
3. Click "Apply" to update the equipment on Strava

## API Endpoints

### Authentication
- `GET /api/auth/login` - Redirect to Strava OAuth
- `GET /api/auth/callback` - OAuth callback handler
- `GET /api/auth/status` - Check authentication status
- `POST /api/auth/logout` - Clear session

### Activities
- `GET /api/activities` - List activities with filters
- `GET /api/activities/{id}` - Get single activity
- `PATCH /api/activities/{id}/equipment` - Update equipment
- `POST /api/activities/sync` - Sync from Strava
- `POST /api/activities/bulk-update` - Bulk update equipment

### Equipment
- `GET /api/equipment` - List all equipment
- `GET /api/equipment/stats` - Get usage statistics
- `GET /api/equipment/{id}` - Get single equipment
- `POST /api/equipment/sync` - Sync from Strava

### Rules
- `GET /api/rules` - List all rules
- `POST /api/rules` - Create rule
- `PUT /api/rules/{id}` - Update rule
- `DELETE /api/rules/{id}` - Delete rule
- `POST /api/rules/{id}/preview` - Preview matching activities
- `POST /api/rules/{id}/apply` - Apply rule to activities

## Development

### Running with Mock Data

To develop the frontend without a backend connection:

```bash
# In frontend/.env
VITE_USE_MOCK_DATA=true
```

This uses the mock data files in `src/data/` for development.

### Project Structure

```
strava-equipment-manager/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings/environment config
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   └── schemas/             # Pydantic schemas
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/              # Vue Router config
│   │   ├── stores/              # Pinia stores
│   │   ├── views/               # Page components
│   │   ├── components/          # Reusable components
│   │   ├── api/                 # API client
│   │   └── data/                # Mock data
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Rule Conditions

### Available Fields
- `name` - Activity name
- `activity_type` - Type (Ride, Run, VirtualRide, etc.)
- `sport_type` - More specific type (GravelRide, TrailRun, etc.)
- `trainer` - Indoor/trainer flag (true/false)
- `device_name` - Recording device name
- `external_id` - External ID (for Zwift, TrainerRoad, etc.)
- `distance` - Distance in meters
- `moving_time` - Moving time in seconds

### Available Operators
- `equals` - Exact match
- `not_equals` - Not equal
- `contains` - String contains
- `not_contains` - String does not contain
- `starts_with` - String starts with
- `ends_with` - String ends with
- `regex` - Regular expression match
- `greater_than` - Numeric greater than
- `less_than` - Numeric less than

## License

MIT
