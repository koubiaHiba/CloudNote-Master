# Deployment Guide — CloudNotes on Azure

## Prerequisites

- GitHub account with the Student Developer Pack verified
- Azure for Students activated ($100 credit, no credit card required)
- Azure CLI installed locally (`az --version` should succeed)
- Docker installed locally
- Git repository pushed to GitHub

---

## Step 1: Create Azure Resources

Run the following commands in your terminal. All resources go in the same region (`westeurope`) so latency and data-residency stay consistent.

```bash
# Log in to your Azure account
az login

# Create a resource group to hold everything
az group create --name cloudnotes-rg --location westeurope

# Create an Azure Container Registry (ACR) — stores your Docker images
az acr create \
  --resource-group cloudnotes-rg \
  --name cloudnotesregistry \
  --sku Basic

# Enable admin access so App Service can pull images
az acr update --name cloudnotesregistry --admin-enabled true

# Print ACR credentials — copy these, you will need them in Step 2
az acr credential show --name cloudnotesregistry

# Create an App Service Plan (Linux, B1 = cheapest paid tier, needed for containers)
az appservice plan create \
  --name cloudnotes-plan \
  --resource-group cloudnotes-rg \
  --is-linux \
  --sku B1

# Create the Web App using your ACR image
az webapp create \
  --resource-group cloudnotes-rg \
  --plan cloudnotes-plan \
  --name cloudnotes-app \
  --deployment-container-image-name cloudnotesregistry.azurecr.io/cloudnotes:latest

# Point the Web App at your ACR (replace <username> and <password> from the credential output above)
az webapp config container set \
  --name cloudnotes-app \
  --resource-group cloudnotes-rg \
  --container-image-name cloudnotesregistry.azurecr.io/cloudnotes:latest \
  --container-registry-url https://cloudnotesregistry.azurecr.io \
  --container-registry-user <username> \
  --container-registry-password <password>

# Enable the /health endpoint as the App Service health-check path
az webapp config set \
  --name cloudnotes-app \
  --resource-group cloudnotes-rg \
  --generic-configurations '{"healthCheckPath": "/health"}'
```

After these commands finish, your app URL will be:
`https://cloudnotes-app.azurewebsites.net`

---

## Step 2: Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

Add the following three secrets:

| Secret name | Where to find the value |
|---|---|
| `ACR_USERNAME` | Output of `az acr credential show` — the `username` field |
| `ACR_PASSWORD` | Output of `az acr credential show` — one of the `passwords` values |
| `AZURE_CREDENTIALS` | JSON output of the `az ad sp create-for-rbac` command below |

To create the `AZURE_CREDENTIALS` service principal:

```bash
# Get your subscription ID
az account show --query id -o tsv

# Create a service principal with Contributor rights on the resource group
az ad sp create-for-rbac \
  --name "cloudnotes-sp" \
  --role contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/cloudnotes-rg \
  --json-auth
```

Copy the entire JSON output and paste it as the value for `AZURE_CREDENTIALS`.

---

## Step 3: Push Code and Trigger the Pipeline

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

Go to your GitHub repository → **Actions** tab. You will see the workflow **"Build and Deploy to Azure"** running. It will:

1. Check out your code
2. Install Python dependencies
3. Run `pytest tests/ -v` — the pipeline fails and stops here if any test fails
4. Build the Docker image and push it to ACR with two tags: the commit SHA and `latest`
5. Authenticate to Azure and deploy the new image to App Service

The first run takes roughly 3–5 minutes.

---

## Step 4: Set Up Azure Monitor Alerts

1. Open the [Azure Portal](https://portal.azure.com) and navigate to your Web App (`cloudnotes-app`).
2. In the left sidebar, click **Monitoring** → **Alerts**.
3. Click **+ Create** → **Alert rule**.

### Alert 1 — HTTP 5xx errors

| Field | Value |
|---|---|
| Signal | HTTP 5xx |
| Condition | Count > 0 |
| Aggregation period | 5 minutes |
| Severity | 2 — Warning |
| Alert rule name | `cloudnotes-5xx-errors` |

### Alert 2 — High response time

| Field | Value |
|---|---|
| Signal | Http Response Time |
| Condition | Average > 5 seconds |
| Aggregation period | 5 minutes |
| Severity | 2 — Warning |
| Alert rule name | `cloudnotes-slow-response` |

For both alerts, create an **Action Group** with your email address so you receive a notification when the alert fires.

Take a screenshot of each configured alert rule for your project report.

---

## Step 5: Verify Everything Works

```bash
# Check the app is live
curl https://cloudnotes-app.azurewebsites.net/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Create a note via the API
curl -X POST https://cloudnotes-app.azurewebsites.net/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello Azure", "content": "Deployed from GitHub Actions!"}'
```

Then open `https://cloudnotes-app.azurewebsites.net` in a browser to confirm the note appears.

To verify CI/CD is working end-to-end, make any small code change (e.g., edit the footer text in `base.html`), commit and push. Watch the Actions tab — within a few minutes the change should appear live at the URL without any manual steps.

---

## Estimated Azure Cost

| Resource | SKU | Estimated cost |
|---|---|---|
| App Service Plan | B1 Linux | ~$13/month |
| Container Registry | Basic | ~$5/month |
| Azure Monitor | Basic alerts | Free tier |
| **Total** | | **~$18/month** |

Your $100 Azure for Students credit covers roughly 5 months. Remember to delete the resource group when the course is over:

```bash
az group delete --name cloudnotes-rg --yes --no-wait
```
