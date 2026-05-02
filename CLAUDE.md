# Cloud Computing Mini-Project — CloudNotes

## What This Project Is
A containerized Python Flask web application deployed on Microsoft Azure, built as a university cloud computing mini-project. The app is a simple notes manager. The real value is the infrastructure: Docker, CI/CD via GitHub Actions, Azure Container Registry, Azure App Service, and Azure Monitor.

## Tech Stack
- **Backend:** Python 3.11, Flask, SQLite (local) / PostgreSQL (production-ready)
- **Frontend:** HTML, CSS, vanilla JavaScript (no framework — keeps it simple)
- **Containerization:** Docker with multi-stage build
- **CI/CD:** GitHub Actions → Azure Container Registry → Azure App Service
- **Cloud:** Microsoft Azure (App Service, Container Registry, Monitor)
- **Observability:** Structured JSON logging (python-json-logger), custom in-memory metrics, live dashboard

## Project Structure
```
cloud-proj/
├── CLAUDE.md
├── README.md
├── DEPLOYMENT_GUIDE.md
├── Dockerfile
├── .dockerignore
├── .github/
│   └── workflows/
│       └── deploy.yml
├── requirements.txt
├── scripts/
│   └── load_test.py
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── metrics.py
│   ├── models.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── about.html
│   │   └── dashboard.html
│   └── static/
│       ├── style.css
│       └── app.js
└── tests/
    └── test_app.py
```

## Documentation
- **COMPLETE_GUIDE.md** — full guide: running locally, deploying to Azure step-by-step, cloud architecture explanation
- **DEPLOYMENT_GUIDE.md** — condensed Azure CLI reference
- **README.md** — project overview and architecture diagram

## Key Commands
- `pip install -r requirements.txt` — install dependencies
- `python -m app.main` — run locally on port 5000
- `docker build -t cloudnotes .` — build container
- `docker run -p 5000:5000 cloudnotes` — run container locally
- `pytest tests/` — run tests
- `python scripts/load_test.py http://localhost:5000` — run load test

## Routes
| Route | Method | Description |
|---|---|---|
| `/` | GET | Notes home page |
| `/about` | GET | Architecture and skills page |
| `/dashboard` | GET | Live metrics dashboard (auto-refreshes every 5s) |
| `/health` | GET | Enhanced health check — version, uptime, memory, note count, environment flags |
| `/metrics` | GET | JSON metrics snapshot — request counters, note operations, avg response time, activity log |
| `/api/notes` | GET | List all notes as JSON |
| `/api/notes` | POST | Create a note |
| `/api/notes/<id>` | GET | Get one note |
| `/api/notes/<id>` | PUT | Update a note |
| `/api/notes/<id>` | DELETE | Delete a note |

## Architecture Decisions
- SQLite for simplicity; the app is stateless enough that data persistence is not the point
- No JS framework — the frontend is intentionally minimal so the focus stays on infrastructure
- Multi-stage Docker build to keep the image small
- GitHub Actions workflow uses OIDC for Azure authentication (no stored passwords)
- Metrics are in-memory — they reset on app restart, which is expected; they exist to make the Azure portal look alive
- JSON logging is configured at the root logger level so Werkzeug request logs are also JSON-structured

## What the Professor Evaluates
1. App is live and accessible from any browser via a public URL
2. Dockerized and deployed to Azure App Service via container
3. CI/CD pipeline: git push → automatic build → automatic deploy
4. Azure Monitor alert configured (HTTP 5xx or response time)
5. Clean README documenting the architecture
6. Structured JSON logs visible in Azure Log Stream
7. Live dashboard at `/dashboard` showing real-time metrics
8. Rich `/health` endpoint used by Azure health checks

## Skills Demonstrated
- **Containerization** — Multi-stage Dockerfile, Gunicorn production server
- **CI/CD Pipeline** — GitHub Actions, automated test → build → deploy
- **Cloud Deployment** — Azure App Service, Azure Container Registry
- **Health Monitoring** — Azure Monitor alerts, rich `/health` endpoint
- **Infrastructure as Code** — reproducible Azure CLI commands in DEPLOYMENT_GUIDE.md
- **Application-level Telemetry** — custom metrics collector, request tracking, operation logging
- **Structured JSON Logging** — every request emits a parseable JSON log line for Azure Log Analytics
- **Custom Metrics & Visualization** — `/metrics` endpoint + live dashboard with CSS bar chart
- **Load Testing** — `scripts/load_test.py` for live demo against Azure URL
