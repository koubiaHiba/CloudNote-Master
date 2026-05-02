# CloudNotes

A containerized Python Flask application deployed on Microsoft Azure — built as a university cloud computing mini-project. The app itself is a simple notes manager; the real deliverable is the infrastructure.

---

## Architecture

```
  Developer
      |
      | git push origin main
      v
 ┌──────────────┐
 │   GitHub     │
 │  Repository  │
 └──────┬───────┘
        │ triggers GitHub Actions workflow
        v
 ┌──────────────────┐
 │  GitHub Actions  │  — installs deps, runs pytest, builds Docker image
 │   CI/CD Pipeline │
 └──────┬───────────┘
        │ docker push  (tagged with commit SHA + latest)
        v
 ┌──────────────────────┐
 │  Azure Container     │
 │  Registry (ACR)      │  — private registry, stores all image versions
 └──────┬───────────────┘
        │ deploy image on push
        v
 ┌──────────────────────┐
 │  Azure App Service   │  — managed Linux container host, public HTTPS URL
 └──────┬───────────────┘
        │ HTTPS
        v
  User's Browser
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3.1, Gunicorn |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Containerization | Docker (multi-stage build) |
| Registry | Azure Container Registry |
| Hosting | Azure App Service (Linux container) |
| CI/CD | GitHub Actions |
| Monitoring | Azure Monitor (HTTP 5xx + response-time alerts) |

---

## Screenshots

> Add screenshots here after deployment:
> - The live app at `https://cloudnotes-app.azurewebsites.net`
> - The GitHub Actions workflow run (green checkmark)
> - Azure Portal showing the running App Service
> - Azure Monitor alert rules configured

---

## Local Development

### Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dev server
python -m app.main
# App available at http://localhost:5000
```

### With Docker

```bash
# Build the image
docker build -t cloudnotes .

# Run the container
docker run -p 5000:5000 cloudnotes
# App available at http://localhost:5000
```

### Run Tests

```bash
pytest tests/ -v
```

---

## Deployment

Full step-by-step instructions including Azure CLI commands, GitHub Secrets setup, and Azure Monitor configuration are in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

**Short version:**
1. Create Azure resources (ACR + App Service) with the CLI commands in the guide
2. Add three GitHub Secrets: `ACR_USERNAME`, `ACR_PASSWORD`, `AZURE_CREDENTIALS`
3. `git push origin main` — the pipeline does everything else

---

## Cloud Services Used

- **Azure App Service** — hosts the Docker container with a public HTTPS endpoint
- **Azure Container Registry** — stores versioned Docker images
- **Azure Monitor** — alerts on HTTP 5xx errors and high response times
- **GitHub Actions** — CI/CD pipeline (test → build → push → deploy)

---

## Project Structure

```
cloud-proj/
├── app/
│   ├── __init__.py
│   ├── main.py          # Flask routes
│   ├── models.py        # In-memory note store
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── about.html
│   └── static/
│       ├── style.css
│       └── app.js
├── tests/
│   └── test_app.py
├── .github/workflows/
│   └── deploy.yml       # CI/CD pipeline
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── DEPLOYMENT_GUIDE.md
└── README.md
```

---

## Author

University cloud computing mini-project.
Built with Flask, Docker, GitHub Actions, and Microsoft Azure.
