# Relayed – Pool Table Control System

FastAPI backend + React frontend for managing pool tables, timers, open sessions, queue, history, ESP32 relay control, and employee management.

## Project Structure

```
Relayed/
├── app/                    # FastAPI backend
│   ├── main.py             # Application entrypoint
│   ├── core/
│   │   └── config.py       # Settings (env vars)
│   ├── db/
│   │   └── database.py     # SQLite init & connections
│   ├── services/
│   │   ├── relay_service.py  # ESP32 HTTP relay control
│   │   └── table_service.py  # Table & queue business logic
│   ├── api/routes/
│   │   ├── auth.py         # Login, logout, user management
│   │   ├── tables.py       # Table control & queue
│   │   ├── history.py      # Session history
│   │   └── system.py       # Health, ESP status, demo mode
│   └── schemas/            # Pydantic request/response models
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── api/client.js   # Axios API client
│   │   ├── context/        # Auth context
│   │   ├── pages/          # Dashboard, History, Employees, System
│   │   └── App.jsx         # Router + Nav
│   └── vite.config.js
├── requirements.txt
└── README.md
```

## Quick Start

### Backend

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) configure via environment variables
export ESP32_HOST=192.168.1.100
export NUM_TABLES=8
export RATE_PER_HOUR=20.0
export DEMO_MODE=true          # set to skip ESP32 contact
export DEFAULT_OWNER_PASSWORD=changeme1

# 3. Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend creates `pool.db` and `auth.db` on first startup and seeds a default **Owner** account using `DEFAULT_OWNER_PASSWORD` (default: `changeme1`).

Interactive docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and log in with the owner password.

### Environment Variables (Backend)

| Variable | Default | Description |
|---|---|---|
| `ESP32_HOST` | `192.168.1.100` | ESP32 IP address |
| `ESP32_PORT` | `80` | ESP32 HTTP port |
| `ESP32_TIMEOUT` | `3.0` | Request timeout (seconds) |
| `DEMO_MODE` | `false` | Skip ESP32, simulate relays |
| `NUM_TABLES` | `8` | Number of pool tables |
| `RATE_PER_HOUR` | `20.0` | Default open-session rate |
| `DB_PATH` | `pool.db` | Main database file |
| `AUTH_DB_PATH` | `auth.db` | Auth database file |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins |
| `DEFAULT_OWNER_NAME` | `Owner` | First owner name |
| `DEFAULT_OWNER_PASSWORD` | `changeme1` | First owner password |

## API Overview

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Login with password |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Current user |
| GET/POST | `/auth/users` | List / create users |
| PUT/DELETE | `/auth/users/{id}` | Update / delete user |
| GET | `/tables` | All table states |
| POST | `/tables/{ch}/start` | Start timed session |
| POST | `/tables/{ch}/open` | Start open (per-hour) session |
| POST | `/tables/{ch}/add-time` | Add minutes to timed session |
| POST | `/tables/{ch}/finish` | Finish session & record history |
| POST | `/tables/{ch}/outage-adjust` | Add time for ESP32 outage |
| GET | `/tables/queue/list` | List queue |
| POST | `/tables/queue/add` | Add to queue |
| DELETE | `/tables/queue/{id}` | Remove from queue |
| POST | `/tables/queue/assign` | Assign queue entry to table |
| GET | `/history` | Session history (filterable) |
| GET | `/system/health` | Health check |
| GET | `/system/esp/status` | ESP32 reachability & status |
| GET/POST | `/system/demo-mode` | Get / toggle demo mode |
| POST | `/system/pending/process` | Retry failed relay commands |

## User Roles

- **Owner** – full access (all pages, system settings)
- **Manager** – tables, history, employee management
- **Employee** – tables and history only
