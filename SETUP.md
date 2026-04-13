# NoDisBot Runbook

This runbook is a task-oriented guide for developers and agents operating this repository.
Use it for common workflows such as local setup, validation, deployment prep, incident triage, and safe Git pushes.

## 1. Project Snapshot

- Project: NoDisBot
- Type: Python Discord bot
- Primary app: `Bot/`
- Legacy code: `v1/`
- External dependency: Notion API
- Current deployment target: Render worker via Docker

Important:

- `Bot/` is the active codebase
- `v1/` is legacy and should not be changed unless explicitly required
- This is a background worker, not a web app

## 2. Key Paths

- Entrypoint: `Bot/bot.py`
- Database config: `Bot/database.py`
- Models: `Bot/models.py`
- Cogs: `Bot/cogs/`
- Business logic: `Bot/functionality/`
- Docker startup: `Dockerfile`
- Runtime entrypoint script: `scripts/render-entrypoint.sh`
- Render config: `render.yaml`
- CI/CD workflow: `.github/workflows/deploy.yml`
- Agent guidance: `AGENTS.md`

## 3. Environment Variables

Required:

- `TOKEN`
- `SECRET_KEY`
- `NOTION_API_KEY`
- `NOTION_DB_ID`
- `OLLAMA_API`

Optional:

- `PREFIX`
- `DATA_DIR`
- `DATABASE_URL`
- `OLLAMA_URL`
- `OLLAMA_MODEL`

Recommended local defaults:

```env
TOKEN=your-discord-bot-token
SECRET_KEY=generate-a-stable-random-secret
NOTION_API_KEY=secret_your_notion_integration_token
NOTION_DB_ID=your_notion_database_id
OLLAMA_API=your_ollama_cloud_api_key
OLLAMA_MODEL=deepseek-v3.1:671b-cloud
PREFIX=!
DATA_DIR=./Bot/database
```

Rules:

- Never commit real secrets
- Keep `SECRET_KEY` stable for existing encrypted records
- If `DATABASE_URL` is set, it overrides local SQLite

## 4. Local Setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
$env:TOKEN="your-discord-bot-token"
$env:SECRET_KEY="generate-a-stable-random-secret"
$env:NOTION_API_KEY="secret_your_notion_integration_token"
$env:NOTION_DB_ID="your_notion_database_id"
$env:OLLAMA_API="your_ollama_cloud_api_key"
$env:OLLAMA_MODEL="deepseek-v3.1:671b-cloud"
$env:PREFIX="!"
$env:DATA_DIR=".\Bot\database"
python Bot\bot.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export TOKEN="your-discord-bot-token"
export SECRET_KEY="generate-a-stable-random-secret"
export NOTION_API_KEY="secret_your_notion_integration_token"
export NOTION_DB_ID="your_notion_database_id"
export OLLAMA_API="your_ollama_cloud_api_key"
export OLLAMA_MODEL="deepseek-v3.1:671b-cloud"
export PREFIX="!"
export DATA_DIR="./Bot/database"
python Bot/bot.py
```

Expected result:

- Bot starts without import errors
- SQLite data directory is created automatically
- Bot logs in to Discord successfully

## 5. First-Time Bot Setup

After the bot is online in Discord:

1. Invite the bot to the target server
2. Run the setup command using the configured prefix
3. Enter:
   - Notion API key
   - Notion database ID
   - whether tagging should be enabled

Expected result:

- Guild configuration is stored locally
- Bot replies with setup success

## 6. Common Verification Tasks

### Check Python syntax

```powershell
python -m compileall Bot
```

### Check Git working tree

```powershell
git status --short
```

### Check for secret files

```powershell
Get-ChildItem -Recurse -Force -File | Where-Object { $_.Name -match '^\.env($|\.)|token\.json|credentials\.json|\.pem$|\.key$|\.pfx$|\.crt$' } | Select-Object FullName
```

### Check for obvious secret patterns in content

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern 'AKIA|AIza|ghp_|github_pat_|sk-[A-Za-z0-9]{20,}|xox[baprs]-|BEGIN (RSA|OPENSSH|PRIVATE)|DISCORD_AUTH=|TOKEN=|SECRET_KEY=|AUTH_KEY=|DATABASE_TOKEN='
```

### Run tests if they exist

```powershell
python -m pytest
```

Note:

- This repository currently has little or no automated test coverage
- Do not overstate confidence if runtime dependencies or secrets are missing

## 7. Docker Validation

Build locally:

```powershell
docker build -t nodisbot:local .
```

Run locally with Docker Compose:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose logs -f nodisbot
```

Optional: verify the Ollama Cloud token from your shell before booting the bot:

```powershell
$headers = @{
  Authorization = "Bearer $env:OLLAMA_API"
  "Content-Type" = "application/json"
}
$body = @{
  model = "deepseek-v3.1:671b-cloud"
  messages = @(@{ role = "user"; content = "Reply with the word ok." })
  stream = $false
} | ConvertTo-Json -Depth 4
Invoke-RestMethod -Method Post -Uri "https://ollama.com/api/chat" -Headers $headers -Body $body
```

Run locally without Compose:

```powershell
docker run --rm `
  -e TOKEN=your-discord-bot-token `
  -e SECRET_KEY=generate-a-stable-random-secret `
  -e NOTION_API_KEY=secret_your_notion_integration_token `
  -e NOTION_DB_ID=your_notion_database_id `
  -e OLLAMA_API=your_ollama_cloud_api_key `
  -e OLLAMA_MODEL=deepseek-v3.1:671b-cloud `
  -e PREFIX=! `
  -e DATA_DIR=/app/data `
  nodisbot:local
```

Expected result:

- container starts
- startup script validates required env vars
- bot process launches as non-root

## 8. Render Deployment Tasks

### Pre-deploy checklist

1. Confirm `render.yaml` exists
2. Confirm `Dockerfile` builds successfully
3. Confirm `TOKEN`, `SECRET_KEY`, `NOTION_API_KEY`, `NOTION_DB_ID`, and `OLLAMA_API` are set in Render
4. Confirm persistent disk is mounted at `/app/data`
5. Confirm `main` branch contains the latest deployment config

### Deploy model

- Service type: worker
- Runtime: Docker
- Persistent disk: required for SQLite persistence

### Required Render secrets

- `TOKEN`
- `SECRET_KEY`
- `NOTION_API_KEY`
- `NOTION_DB_ID`
- `OLLAMA_API`

### Safe Render defaults

- `DATA_DIR=/app/data`
- `PREFIX=!`
- `OLLAMA_URL=https://ollama.com`
- `OLLAMA_MODEL=deepseek-v3.1:671b-cloud`
- auto-deploy enabled

## 9. GitHub Push Procedure

### Pre-push checklist

1. Review staged files
2. Check for secrets
3. Ensure `.env` is not staged
4. Ensure database files are not staged
5. Confirm only intended source/config files are included

### Safe commit sequence

```powershell
git status
git add .
git commit -m "Describe the change clearly"
git branch -M main
git push -u origin main
```

If remote is missing:

```powershell
git remote add origin <repo_url>
git push -u origin main
```

If remote already exists:

```powershell
git remote -v
git remote set-url origin <repo_url>
git push -u origin main
```

## 10. Incident Triage

### Symptom: Bot exits immediately

Check:

- `TOKEN` is set
- `SECRET_KEY` is set
- dependencies are installed
- Discord token is valid

Commands:

```powershell
python --version
pip install -r requirements.txt
git status --short
```

### Symptom: Bot starts but setup/search/add fails

Check:

- Notion API key is valid
- Notion database ID is valid
- Notion integration has access to the database
- `SECRET_KEY` was not changed after credentials were stored

### Symptom: Existing guild config no longer works

Likely causes:

- `SECRET_KEY` changed
- local SQLite file changed or was lost
- Render disk not mounted

### Symptom: Data resets after deploy/restart

Likely causes:

- app is writing to ephemeral filesystem
- `DATA_DIR` is not pointing to mounted storage
- Render persistent disk is missing or misconfigured

## 11. Safe Editing Priorities

When making improvements, prefer this order:

1. Secret-safe logging
2. Better error handling for Notion API calls
3. Input validation and startup validation
4. Deployment reliability
5. Slash command support
6. Pagination and UX improvements
7. Storage migration from SQLite to Postgres
8. Automated tests

## 12. Known Operational Risks

- `v1/` contains outdated and less secure patterns
- Current codebase has limited automated tests
- Some active code still uses broad `except:` blocks
- Notion API failures are not consistently surfaced
- SQLite is acceptable for a single worker but not ideal for scale

## 13. Recommended Next Operational Improvements

- remove secret-bearing debug prints from active code
- add request timeouts to all outbound HTTP calls
- replace broad `except:` blocks in touched files
- add smoke tests for startup and env validation
- add a migration path to Render Postgres
- add branch protection and CI enforcement on `main`
