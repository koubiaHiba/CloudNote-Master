# CloudNotes — Complete Guide

This guide covers everything from running the app on your laptop to deploying it live on Microsoft Azure and understanding how the cloud infrastructure works. Follow the steps in order. Every command is explained so you know what it does, not just that it works.

---

# Part 1 — Running CloudNotes on Your Machine

There are two ways to run the app locally. Option A is faster and easier. Option B mirrors production exactly and is important to try at least once before deploying.

---

## Option A: Run Without Docker (Fastest for Development)

### Prerequisites

Before starting, verify you have the following installed:

```bash
python --version    # Must be 3.11 or higher
pip --version       # Comes with Python
git --version       # Any recent version
```

If `python` shows version 2.x, try `python3 --version`. On Linux/macOS, `python` often points to Python 2. Wherever this guide says `python`, use `python3` if needed.

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/cloudnotes.git
```

This downloads a full copy of the project to your machine.

```bash
cd cloudnotes
```

All commands from here must be run from inside this folder.

---

### Step 2: Create a Virtual Environment

A virtual environment keeps this project's Python packages separate from everything else on your system. This avoids version conflicts.

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

After activation, your terminal prompt changes to show `(venv)` at the start. That means it is active.

> ⚠️ **Windows PowerShell note:** If you get a "running scripts is disabled" error, run this first:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask (the web framework), Gunicorn (the production web server), pytest (the test runner), psutil (for memory metrics), python-json-logger (for structured logging), and requests (for the load test script).

---

### Step 4: Run the App

```bash
python -m app.main
```

You should see output like:

```
 * Serving Flask app 'main'
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

> ✅ **Checkpoint:** Open your browser at **http://localhost:5000** — you should see the CloudNotes home page with a form to add notes.

---

### Step 5: Run the Tests

Open a second terminal, activate the virtual environment again, and run:

```bash
pytest tests/ -v
```

You should see 11 tests all passing with green `PASSED` labels.

---

### Step 6: Explore the Routes

With the app running, open these URLs in your browser:

| URL | What it shows |
|---|---|
| `http://localhost:5000/` | The main notes page — add, edit, delete notes |
| `http://localhost:5000/about` | Architecture page — the professor reads this to understand the project |
| `http://localhost:5000/dashboard` | Live metrics dashboard — updates every 5 seconds |
| `http://localhost:5000/health` | Health check JSON — shows version, uptime, memory usage, note count |
| `http://localhost:5000/metrics` | Raw JSON metrics — all counters and the last 10 requests |

---

### Troubleshooting (Option A)

**"Port 5000 is already in use"**

Run on a different port by setting the PORT environment variable:

```bash
# Linux / macOS
PORT=8080 python -m app.main

# Windows Command Prompt
set PORT=8080 && python -m app.main

# Windows PowerShell
$env:PORT=8080; python -m app.main
```

Then open `http://localhost:8080` instead.

**"Permission denied" or "python: command not found"**

Use `python3` instead of `python`. On most Linux systems, `python3` is the correct command.

**"ModuleNotFoundError: No module named 'flask'"**

Your virtual environment is not activated. Run `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate.bat` (Windows) and try again.

---

## Option B: Run With Docker (Mirrors Production Exactly)

Docker packages your app, Python, and all dependencies into a single portable image. This is the exact same image that runs on Azure. Testing it here confirms that if it works locally in Docker, it will work on Azure.

### Prerequisites

Install Docker Desktop from https://docs.docker.com/get-docker/ — it is available for Linux, macOS, and Windows. After installing, make sure it is running (on Linux, run `sudo systemctl start docker`).

Verify:
```bash
docker --version    # Should print Docker version 20.x or higher
```

---

### Step 1: Build the Docker Image

```bash
docker build -t cloudnotes .
```

This reads the `Dockerfile` in the project root, which uses a two-stage build:
- **Stage 1** installs Python dependencies into an isolated layer
- **Stage 2** copies only the app code and the installed packages, leaving out everything else

The result is a lean production image. The `-t cloudnotes` flag gives it the name `cloudnotes`.

The first build takes 1–3 minutes (it downloads the Python base image). Subsequent builds are much faster due to Docker layer caching.

---

### Step 2: Run the Container

```bash
docker run -p 5000:5000 cloudnotes
```

The `-p 5000:5000` maps port 5000 on your machine to port 5000 inside the container. The app starts using Gunicorn with 4 workers (the same configuration used on Azure).

> ✅ **Checkpoint:** Open **http://localhost:5000** — the app works the same as Option A, but now it is running inside a container.

---

### Step 3: Stop the Container

Open a new terminal and find the running container:

```bash
docker ps
```

This lists all running containers. Find the one named `cloudnotes` and copy its `CONTAINER ID` (the short hex string in the first column). Then stop it:

```bash
docker stop <CONTAINER_ID>
```

Alternatively, press `Ctrl+C` in the terminal where the container is running.

---

### Troubleshooting (Option B)

**"Port 5000 is already in use"**

Map to a different host port:

```bash
docker run -p 8080:5000 cloudnotes
```

Then open `http://localhost:8080`.

**"Cannot connect to the Docker daemon"**

Docker Desktop is not running. Start it from your Applications menu (macOS/Windows) or run `sudo systemctl start docker` (Linux).

**"docker build" fails mid-way**

Check that Docker has at least 2 GB of free disk space. Run `docker system prune` to clean up old images and try again.

---

# Part 2 — Deploying to Microsoft Azure

This section deploys the app to the cloud so it is accessible from anywhere in the world via a public URL. Read each step fully before running commands.

---

## Step 1: Get Your Free Azure Credits

> ⚠️ **Important:** Use `azure.microsoft.com/free/students`, **not** `azure.microsoft.com/free`. The students page gives you $100 credit with no credit card required. The regular free page does require a credit card.

1. Go to **https://education.github.com**
2. Click **"Join GitHub Education"** (or "Get your pack" if you already have a GitHub account)
3. Enter your **university email address** — this must be the address your institution gave you (e.g., `you@university.ac.ma`)
4. If prompted, upload a photo of your student ID card or proof of enrollment
5. Wait for approval — this can take anywhere from a few minutes to a few days
6. Once approved, go back to **https://education.github.com/pack**
7. Find the **Microsoft Azure** tile and click the offer link — it takes you to Azure for Students
8. Sign in with a Microsoft account. If your university email is a Microsoft/Outlook account, use it directly. Otherwise, create a free Microsoft account at https://account.microsoft.com
9. Confirm you see **"$100 Azure credit"** and **"No credit card required"** before completing signup
10. Complete the signup flow — when finished, you have an **Azure for Students** subscription

> ✅ **Checkpoint:** You should receive a confirmation email and be able to log in at https://portal.azure.com

---

## Step 2: Install the Azure CLI

The Azure CLI lets you control Azure from your terminal instead of clicking through the portal. Every action in this guide uses the CLI because it is faster and reproducible.

**Linux (Ubuntu/Debian):**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**macOS:**
```bash
brew install azure-cli
```

If you do not have Homebrew, install it first from https://brew.sh

**Windows:**
```cmd
winget install Microsoft.AzureCLI
```

Or download the installer from https://aka.ms/installazurecliwindows

---

### Log in to Azure

```bash
az login
```

This opens a browser window where you sign in with the same Microsoft account you used to register for Azure for Students. After signing in, return to the terminal.

---

### Verify your subscription

```bash
az account show
```

This prints information about your active subscription. Look for your subscription name and confirm the `state` is `"Enabled"`. If you have multiple subscriptions, set the correct one:

```bash
az account set --subscription "Azure for Students"
```

> ✅ **Checkpoint:** Running `az account show` returns your subscription without errors.

---

## Step 3: Push Your Code to GitHub

Azure deployment reads from GitHub. You need the code in a GitHub repository before the pipeline can work.

### Create the repository

1. Go to **https://github.com** and sign in
2. Click the **+** icon in the top-right corner → **New repository**
3. Name it `cloudnotes`
4. Choose **Public** or **Private** (either works)
5. **Do NOT** check "Add a README file" — you already have one
6. Click **Create repository**

### Push the code

Run these commands from inside your project folder:

```bash
git init
```
Initializes a new git repository in the project folder (skip if you already ran this).

```bash
git add .
```
Stages all project files for the first commit.

```bash
git commit -m "CloudNotes - Cloud Computing Mini-Project"
```
Creates the first commit with a descriptive message.

```bash
git branch -M main
```
Renames the default branch to `main` (GitHub's current default).

```bash
git remote add origin https://github.com/YOUR_USERNAME/cloudnotes.git
```
Connects your local repository to the GitHub repository. Replace `YOUR_USERNAME` with your actual GitHub username.

```bash
git push -u origin main
```
Uploads all your code to GitHub. The `-u` flag sets `origin main` as the default push target so future `git push` commands work without arguments.

> ✅ **Checkpoint:** Refresh your GitHub repository page — you should see all your project files listed.

---

## Step 4: Create Azure Resources

You need three Azure resources: a **Container Registry** (stores Docker images), an **App Service Plan** (the virtual machine), and a **Web App** (the running application). The commands below create all three.

---

```bash
az group create --name cloudnotes-rg --location westeurope
```

Creates a **resource group** — think of it as a folder that holds all Azure resources for this project. Using `westeurope` puts the server in Western Europe. You can use `eastus` or `southeastasia` if you prefer.

---

```bash
az acr create --resource-group cloudnotes-rg --name cloudnotesregistry --sku Basic
```

Creates an **Azure Container Registry** — a private storage location for your Docker images. Every time GitHub Actions builds a new image, it pushes it here. The `--sku Basic` is the cheapest tier (~$5/month).

> ⚠️ **Registry names must be globally unique.** If this command fails with "name already taken," add your initials or a number: `cloudnotesregistry-ysf` or `cloudnotesregistry42`. Then update `ACR_NAME` in `.github/workflows/deploy.yml` to match.

---

```bash
az acr update --name cloudnotesregistry --admin-enabled true
```

Enables **admin access** on the registry. By default, only Azure services can authenticate to ACR. This creates a username/password that GitHub Actions can use to push images.

---

```bash
az appservice plan create \
  --name cloudnotes-plan \
  --resource-group cloudnotes-rg \
  --is-linux \
  --sku B1
```

Creates an **App Service Plan** — the underlying virtual machine. `--is-linux` is required for Docker containers. `--sku B1` is the cheapest plan that supports containers (~$13/month). The Free tier (F1) does not support custom containers.

---

```bash
az webapp create \
  --resource-group cloudnotes-rg \
  --plan cloudnotes-plan \
  --name cloudnotes-app \
  --deployment-container-image-name cloudnotesregistry.azurecr.io/cloudnotes:latest
```

Creates the **Web App** — the actual running application. Azure assigns it a public URL: `https://cloudnotes-app.azurewebsites.net`. The `--deployment-container-image-name` tells it which Docker image to run.

> ⚠️ **App names must also be globally unique.** If this fails with "name already taken," use `cloudnotes-app-ysf` or `cloudnotes-app-42`. Then update `AZURE_WEBAPP_NAME` in `.github/workflows/deploy.yml` to match.

> ✅ **Checkpoint:** All four commands completed without errors. You now have Azure resources, but the app is not running yet — that happens after the first deployment.

---

## Step 5: Get Credentials for GitHub Actions

GitHub Actions needs credentials to push images to your Container Registry and to tell Azure to deploy. You get these credentials now and store them as GitHub Secrets in the next step.

### Get the Container Registry credentials

```bash
az acr credential show --name cloudnotesregistry
```

This prints a JSON block with a `username` and two `passwords`. Save these values — you need them shortly. Use either password; both work.

---

### Create a Service Principal

A service principal is a "robot account" — a special identity that GitHub Actions uses to talk to Azure. It has limited permissions (only to deploy to this resource group) and does not have access to your personal Azure account.

```bash
az ad sp create-for-rbac \
  --name "cloudnotes-github-deployer" \
  --role contributor \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/cloudnotes-rg \
  --json-auth
```

This prints a JSON block that looks like:

```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**Copy the entire JSON block** — all lines including the curly braces. You need the whole thing in the next step.

---

## Step 6: Add Secrets to GitHub

1. Go to your GitHub repository page
2. Click **Settings** (the gear icon in the top navigation)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **"New repository secret"** and add these three secrets one at a time:

| Secret Name | Value |
|---|---|
| `ACR_USERNAME` | The `username` value from the `az acr credential show` output |
| `ACR_PASSWORD` | One of the `passwords` values from the same output |
| `AZURE_CREDENTIALS` | The complete JSON block from the service principal command |

After saving each secret, GitHub shows it as a redacted entry. You cannot view the value again after saving — if you lose it, delete the secret and recreate it.

> ⚠️ **Never paste these credentials into your code or commit them to git.** Storing secrets in GitHub Secrets is the correct and safe way to use them in CI/CD.

> ✅ **Checkpoint:** Your repository's Secrets page shows three secrets: `ACR_USERNAME`, `ACR_PASSWORD`, and `AZURE_CREDENTIALS`.

---

## Step 7: Configure the Web App to Pull From Your Registry

Tell the Web App exactly which registry and image to use, and give it the credentials to pull:

```bash
az webapp config container set \
  --name cloudnotes-app \
  --resource-group cloudnotes-rg \
  --container-image-name cloudnotesregistry.azurecr.io/cloudnotes:latest \
  --container-registry-url https://cloudnotesregistry.azurecr.io \
  --container-registry-user <USERNAME_FROM_STEP_5> \
  --container-registry-password <PASSWORD_FROM_STEP_5>
```

Replace `<USERNAME_FROM_STEP_5>` and `<PASSWORD_FROM_STEP_5>` with the actual values from Step 5.

---

```bash
az webapp config appsettings set \
  --name cloudnotes-app \
  --resource-group cloudnotes-rg \
  --settings WEBSITES_PORT=5000
```

Tells Azure App Service which port your app listens on. Without this, Azure tries port 80 by default and the health check fails.

---

## Step 8: Trigger the First Deployment

Push any change to trigger the GitHub Actions pipeline. If you have not changed anything since the initial push, make a tiny change (add a space to the README) to create a new commit:

```bash
git add .
git commit -m "Trigger first Azure deployment"
git push origin main
```

### Watch the pipeline run

1. Go to your GitHub repository
2. Click the **Actions** tab at the top
3. You should see a workflow run called **"Build and Deploy to Azure"** with a yellow spinning icon (in progress)
4. Click on it to see the individual steps running in real time:
   - **Checkout code** — downloads your code to the GitHub Actions runner
   - **Set up Python** — installs Python 3.11
   - **Run tests** — runs `pytest tests/ -v` (if this fails, deployment stops and nothing is deployed)
   - **Login to Azure Container Registry** — authenticates using your secrets
   - **Build and push Docker image** — builds the image and pushes it to ACR with two tags
   - **Login to Azure** — authenticates the deployer service principal
   - **Deploy to Azure Web App** — tells App Service to use the new image

The full pipeline takes 2–5 minutes on first run.

**If you see a green checkmark:** your app is deployed and live.

**If you see a red X:** click on the failed step to see the error log. Common causes:
- Wrong secret values — go back to Step 6 and re-enter them
- Name mismatch — the `AZURE_WEBAPP_NAME` or `ACR_NAME` in `deploy.yml` does not match what you created in Step 4

> ✅ **Checkpoint:** The Actions tab shows a green checkmark next to your workflow run.

---

## Step 9: Verify the Live App

Open your app in a browser. If you used the default name:

```
https://cloudnotes-app.azurewebsites.net
```

If you used a custom name, replace `cloudnotes-app` with your name.

**Verify it works:**

1. Create a note — type a title and content, click Save Note
2. The note should appear in the grid below the form
3. Open `/dashboard` — you should see the metrics dashboard with live counters
4. Open `/health` — the response should include `"azure": true` (Azure App Service sets an environment variable that the app detects)

**Verify it is accessible from anywhere:**

Open the URL on your phone using mobile data (turn off WiFi). If it loads, the app is truly publicly accessible — not just on your local network.

**Verify the health check:**

```bash
curl https://cloudnotes-app.azurewebsites.net/health
```

Expected response (abbreviated):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 120.5,
  "checks": {
    "memory_usage_mb": 45.2,
    "note_count": 3,
    "total_requests_served": 15
  },
  "environment": {
    "python_version": "3.11.x",
    "container": true,
    "azure": true
  }
}
```

> ✅ **Checkpoint:** The app loads at the public URL, `/health` returns `"azure": true`, and you can create/view notes from a phone.

---

## Step 10: Set Up Azure Monitor Alerts

Monitoring alerts make the Azure Portal dashboard look impressive and demonstrate production-readiness. Set up two alerts: one for errors and one for slow responses.

### Navigate to your Web App

1. Go to **https://portal.azure.com**
2. Type `cloudnotes-app` in the search bar at the top
3. Click on your Web App in the results

### Create Alert 1 — HTTP 5xx Errors

1. In the left sidebar, click **Monitoring** → **Alerts**
2. Click **+ Create** → **Alert rule**
3. Under **Condition**, click **"Add condition"**
4. In the search box, type `Http Server Errors` and select it
5. Set the condition to: **Count** → **Greater than** → `0`
6. Set **Aggregation granularity** to **5 minutes**
7. Click **Next: Actions**
8. Click **Create action group**
   - Action group name: `email-alerts`
   - Display name: `email-alerts`
   - Under **Notifications**, choose **Email/SMS/Push/Voice**
   - Enter your email address
   - Click **OK**
9. Click **Next: Details**
10. Alert rule name: `HTTP 5xx Alert`
11. Severity: **2 — Warning**
12. Click **Review + Create** → **Create**

### Create Alert 2 — High Response Time

Repeat the same steps with these differences:
- Condition: **Response Time** → **Average** → **Greater than** → `5` (seconds)
- Alert rule name: `Slow Response Alert`

### View Metrics Charts

1. In the left sidebar, click **Monitoring** → **Metrics**
2. Click **+ Add metric**
3. Select **Requests** from the dropdown
4. You now see a chart of incoming HTTP requests over time

> ⚠️ **Take screenshots** of:
> - The Alerts page showing both alert rules
> - The Metrics chart showing requests
> - The Log Stream (left sidebar → Monitoring → Log stream) — this shows JSON-structured log lines in real time

These screenshots go in your project report.

---

## Running the Load Test (For the Demo)

The load test script creates, updates, and deletes notes rapidly so the metrics and charts show real activity during your demo.

**Against the live Azure app:**
```bash
python scripts/load_test.py https://cloudnotes-app.azurewebsites.net
```

While this runs, open `/dashboard` in another browser tab. You will see the total requests counter climbing, the bar chart updating, and the activity log filling in — in real time. This is the demo moment.

---

# Part 3 — Understanding the Cloud Architecture

This section explains what is actually happening behind the scenes. Read this before your presentation or viva.

---

## Section 1: The Deployment Pipeline

Every time you push code to GitHub, this sequence of events happens automatically:

```
YOU (developer)
  │
  ├── git push origin main
  │
  ▼
GITHUB (code repository)
  │
  └── detects push to main branch
      │
      ▼
GITHUB ACTIONS (CI/CD automation)
  │
  ├── Step 1: Checks out your code onto a fresh virtual machine
  ├── Step 2: Installs Python 3.11 and runs pytest
  │             └── If ANY test fails → pipeline stops, nothing is deployed
  ├── Step 3: Builds a Docker image from your Dockerfile
  ├── Step 4: Pushes the image to Azure Container Registry
  │             └── Two tags: the commit SHA (e.g., a3f9b2c) and "latest"
  └── Step 5: Calls the Azure API to update the Web App
              └── "Deploy image cloudnotesregistry.azurecr.io/cloudnotes:a3f9b2c"
  │
  ▼
AZURE CONTAINER REGISTRY (private Docker registry)
  │
  ├── Stores every image version by commit SHA
  └── "latest" tag always points to the most recent successful build
  │
  ▼
AZURE APP SERVICE (managed web server)
  │
  ├── Pulls the new image from ACR
  ├── Starts the new container alongside the old one
  ├── Sends a health check request to /health
  │     ├── If response is 200 OK → switches traffic to new container, stops old one
  │     └── If response is not 200 → keeps old container running, new deployment fails safely
  │
  ▼
USER (anywhere in the world)
  │
  └── Opens https://cloudnotes-app.azurewebsites.net
```

---

### What is a Container Registry?

Think of it as a private Docker Hub, but owned by you and hosted on Azure. When GitHub Actions runs `docker push`, the image is uploaded here. When App Service deploys, it runs `docker pull` from here.

Tagging images with the git commit SHA means you have a complete history. If a deployment breaks the app, you can roll back by pointing App Service at an earlier image tag. The `latest` tag always reflects the most recently deployed version.

---

### What is Azure App Service?

App Service is a managed platform for running web applications. "Managed" means:

- You do not configure a Linux server
- You do not install Python or manage security patches
- You do not set up HTTPS certificates (Azure handles this automatically)
- You do not configure a load balancer or a reverse proxy

You give App Service a Docker image, and it runs it. It assigns a public URL (`*.azurewebsites.net`), handles incoming HTTPS traffic, restarts the container if it crashes, and runs health checks against `/health` to confirm the app is alive.

On the B1 tier, you get one virtual machine. If you needed to handle much more traffic, you could scale out to 10 instances with one CLI command — App Service manages the load balancing automatically.

---

### What is GitHub Actions?

GitHub Actions is an automation system built into GitHub. You write a workflow file (`.github/workflows/deploy.yml`) that describes a sequence of steps. GitHub runs those steps on a fresh virtual machine every time a specified event occurs (in this case: a push to the `main` branch).

The professor can see every deployment in the Actions tab. Each run shows: which commit triggered it, whether it succeeded or failed, how long it took, and the full output of every step. This is the primary audit trail for CI/CD — it proves that deployments are automated and not manual.

---

## Section 2: What Happens When a User Opens the App

Tracing a single HTTP request from browser to server and back:

1. **User types** `https://cloudnotes-app.azurewebsites.net` in their browser
2. **DNS lookup** — the browser asks a DNS server what IP address `cloudnotes-app.azurewebsites.net` maps to. Azure manages this DNS entry automatically.
3. **TCP connection** — the browser connects to Azure's edge network over HTTPS. Azure handles the TLS certificate.
4. **Azure load balancer** — forwards the request to your App Service instance
5. **App Service** — passes the request to your running Docker container
6. **Gunicorn (inside the container)** — receives the raw HTTP request and passes it to Flask
7. **Flask routes the request** — matches `GET /` to the `index()` function in `app/main.py`
8. **`@app.before_request`** fires — records the start time and generates a unique request ID (UUID)
9. **`index()`** calls `models.get_all_notes()` — retrieves the in-memory list of notes
10. **`render_template("index.html")`** — Jinja2 fills in the HTML template with the notes data
11. **`@app.after_request`** fires — logs the request as JSON, records metrics, adds `X-Request-ID` header to the response
12. **Flask returns HTML** → Gunicorn → App Service → Azure → user's browser
13. **Browser parses HTML** — finds `<link>` and `<script>` tags, makes additional requests for `style.css` and `app.js`
14. **`app.js` runs** — calls `fetch("/health")` to check if the app is alive and update the status dot, then calls `fetch("/api/notes")` to load notes dynamically

Every single step from 1 to 11 happens in under 100 milliseconds for a healthy deployment.

---

## Section 3: What the Professor Sees in the Azure Portal

When you log in to https://portal.azure.com and open your Web App, you see a set of "blades" (sections) in the left sidebar. Here is what each one shows and why it matters:

| Blade | Location | What it shows |
|---|---|---|
| **Overview** | Top of the sidebar | Public URL, running status, resource group, region, App Service Plan tier, CPU/memory sparklines |
| **Deployment Center** | Deployment section | Which container image is currently running, the last deployment time and status |
| **Log stream** | Monitoring section | Live tail of application logs — this is where the JSON-structured request logs appear in real time |
| **Metrics** | Monitoring section | Charts for HTTP requests, response times, CPU usage, memory usage. Spikes during the load test are visible here |
| **Alerts** | Monitoring section | The two alert rules you configured — HTTP 5xx and response time |
| **Health check** | Monitoring section | Whether the `/health` endpoint is responding and what it returned |
| **Configuration** | Settings section | Environment variables (`WEBSITES_PORT=5000`), container image settings, port mappings |

**Log stream is the most impressive blade to demo.** Open it in the Azure Portal, then create a note or run the load test. You will see JSON log lines appearing in real time:

```json
{"asctime": "2026-04-18T10:30:00", "levelname": "INFO", "name": "cloudnotes",
 "message": "request", "method": "POST", "path": "/api/notes",
 "status": 201, "response_time_ms": 12.3, "request_id": "a1b2c3d4-..."}
{"asctime": "2026-04-18T10:30:00", "levelname": "INFO", "name": "cloudnotes",
 "message": "NOTE_CREATED", "id": 5, "title": "My note", "timestamp": "2026-04-18T..."}
```

Azure Log Analytics can query these logs with KQL (Kusto Query Language) to answer questions like "how many 500 errors happened in the last hour?" — but even in the raw Log Stream view it clearly demonstrates structured, machine-parseable logging.

---

## Section 4: Why This Architecture Matters

These are the key cloud computing concepts your project demonstrates. Use this section to explain your work in a viva or presentation.

---

### Containerization

The app runs identically on your laptop and in the cloud because Docker packages everything into a single image: the Python runtime, all pip packages, and the app code. There is no "but it works on my machine" problem.

The multi-stage Dockerfile is a production practice: Stage 1 installs dependencies (large, messy), Stage 2 copies only what is needed to run (small, clean). The resulting image is roughly 150 MB instead of 500+ MB.

---

### CI/CD (Continuous Integration / Continuous Deployment)

Traditional deployment: developer writes code → manually SSHs into a server → copies files → restarts the process → hopes it works.

This project's deployment: developer writes code → `git push` → tests run automatically → Docker image builds → Azure deploys → done. Zero manual steps after initial setup.

This is how production software ships at real companies — the pipeline runs hundreds of times per day, and no human touches the production server directly.

---

### Infrastructure as Code

The Azure CLI commands in this guide define the infrastructure. Instead of clicking through the Azure Portal, you run scripts. This means:

- **Reproducible:** anyone can recreate the exact same infrastructure by running the same commands
- **Version-controllable:** you can commit the commands to git alongside the application code
- **Auditable:** the commands are documentation — they show exactly what was created and how

At larger scale, tools like Terraform or Bicep formalize this further — but the principle is the same.

---

### Observability

Observability means being able to answer "what is the system doing right now?" without SSH-ing into a server.

This project has three layers of observability:

1. **Logs** — every request emits a structured JSON log line. Logs tell you *what happened*.
2. **Metrics** — `/metrics` exposes counters and averages. Metrics tell you *how the system is performing*.
3. **Health checks** — `/health` returns a structured JSON payload. Health checks tell you *is the system alive?*

Together these make the app **observable** — you have visibility into it from the outside without needing to look at source code or log in to the server.

---

### Scalability

Azure App Service can scale from 1 to 10+ instances with a single command. The app is **stateless** (notes are in memory, not a database), which is the correct pattern for horizontal scaling: any instance can handle any request because there is no session state tied to a specific server.

In production, you would replace in-memory storage with **Azure Database for PostgreSQL** or **Azure Cosmos DB** so notes persist across restarts and across multiple instances. The app's architecture already supports this — swapping `models.py` for a database-backed version would not require changes to `main.py` or the infrastructure.

---

## Section 5: Cost Breakdown

Your Azure for Students account gives you $100 USD credit.

| Resource | Tier | Estimated monthly cost |
|---|---|---|
| Azure Container Registry | Basic | ~$5 |
| Azure App Service | B1 (Linux) | ~$13 |
| Azure Monitor alerts | Basic tier | Free |
| Azure Log Analytics | First 5 GB/month | Free |
| **Total** | | **~$18/month** |

Your $100 covers roughly **5 months** at this level.

---

### Pause the app when you are not using it

When the project is done being graded, stop the Web App to stop billing:

```bash
az webapp stop --name cloudnotes-app --resource-group cloudnotes-rg
```

This stops the App Service instance. The ACR storage still costs ~$5/month even when stopped.

To restart later:

```bash
az webapp start --name cloudnotes-app --resource-group cloudnotes-rg
```

---

### Delete everything when the course is over

This deletes all resources in the resource group permanently:

```bash
az group delete --name cloudnotes-rg --yes --no-wait
```

The `--no-wait` flag returns control to your terminal immediately while Azure deletes the resources in the background. Deletion takes 1–2 minutes. After this, you will no longer be billed.

> ⚠️ **This cannot be undone.** All resources, all stored images, and all logs are permanently deleted. Only run this when you are completely finished with the project.

---

*This guide covers everything needed to run, deploy, and understand CloudNotes. If a step fails, the error message from the Azure CLI or GitHub Actions usually explains exactly what went wrong — read it carefully before asking for help.*
