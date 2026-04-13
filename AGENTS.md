# NoDisBot Agent Guide

This document is the operational reference for AI/code agents working in this repository.
Follow it strictly unless the user explicitly asks for a different approach.

## 1. Project Identity

- Project type: Python Discord bot
- Primary purpose: Save, search, delete, and upload resources from Discord into a Notion database
- Active application path: `Bot/`
- Legacy code path: `v1/`
- Deployment target: Render background worker using Docker

Treat `Bot/` as the production codebase.
Treat `v1/` as legacy/reference-only code unless the user explicitly asks to modify it.

## 2. Source of Truth

When reasoning about the application, prefer these files:

- Entrypoint: `Bot/bot.py`
- DB config: `Bot/database.py`
- Data model: `Bot/models.py`
- Discord command handlers: `Bot/cogs/`
- Core business logic: `Bot/functionality/`
- Container runtime: `Dockerfile`
- Render deploy config: `render.yaml`
- CI/CD: `.github/workflows/deploy.yml`
- Startup validation: `scripts/render-entrypoint.sh`
- Environment template: `.env.example`

## 3. Architecture Summary

The application is a single-process Discord worker with these layers:

1. Discord bot entrypoint in `Bot/bot.py`
2. Command cogs in `Bot/cogs/`
3. Helper/service code in `Bot/functionality/`
4. Local persistence for guild configuration via SQLite in `Bot/database.py`
5. External integration with the Notion API

There is no HTTP server in the active app.
Do not assume ports, health endpoints, or web routing exist.

## 4. Runtime and Deployment Assumptions

- Python runtime target: 3.8
- Dependency source: `requirements.txt`
- Service type on Render: `worker`
- Persistent storage: required if using SQLite
- Default persistent data path: `/app/data` in containers
- Local data path can be controlled with `DATA_DIR`
- `DATABASE_URL` overrides SQLite entirely when set

The active code now expects one of:

- `DATABASE_URL`
- or a writable `DATA_DIR`

## 5. Required Environment Variables

Required:

- `TOKEN`
- `SECRET_KEY`

Optional:

- `PREFIX`
- `DATA_DIR`
- `DATABASE_URL`

Rules:

- Never hardcode real secrets
- Never commit `.env`
- Never print decrypted credentials or tokens
- Fail fast when required env vars are missing

## 6. Current Deployment Standard

This repo is configured for Docker-based deployment on Render.

Expected files:

- `Dockerfile`
- `render.yaml`
- `.github/workflows/deploy.yml`
- `.dockerignore`
- `.gitignore`

Deployment model:

- Build Docker image from repo root
- Run `python -u Bot/bot.py`
- Mount persistent disk to `/app/data`
- Store secrets in Render environment variables

## 7. Agent Working Rules

### Scope

- Prefer modifying `Bot/` over `v1/`
- Do not remove legacy code unless the user asks
- Do not rewrite the project into another framework unless explicitly requested

### Safety

- Check for secrets before staging or pushing
- Do not commit `.env`, database files, credentials, or tokens
- Avoid logging secrets, Notion credentials, or decrypted values
- Prefer non-destructive changes

### Quality

- Keep changes minimal and targeted
- Preserve current project structure unless a structural refactor is requested
- Add small, useful comments only when needed
- Prefer explicit errors over silent `except:` blocks when editing touched code

### Deployment

- This bot is a background worker, not a web service
- Do not add `EXPOSE` or HTTP health endpoints unless the user explicitly asks for a web layer
- Keep Docker images minimal and non-root

## 8. Repository Hygiene Rules

Never commit:

- `.env`
- `*.sqlite`
- `*.sqlite3`
- `token.json`
- `credentials.json`
- `google-credentials.json`
- private keys/certs
- local virtual environments
- caches/logs

Before any push:

1. Review `git status`
2. Check for secrets or credential files
3. Confirm only intended files are staged

## 9. Known Risks in the Codebase

Agents should keep these in mind:

- `v1/` contains insecure and outdated patterns
- The active project has little/no test coverage
- Some runtime paths still use broad exception handling
- Notion API error handling is incomplete in several paths
- SQLite is acceptable for single-worker deployment but not ideal for scale

When improving the code, prioritize:

1. secret-safe logging
2. better error handling
3. startup/env validation
4. safer persistence and migrations
5. tests around critical bot flows

## 10. Recommended Verification Commands

Use these when relevant:

```powershell
python -m compileall Bot
git status --short
Get-ChildItem -Recurse -Force -File | Where-Object { $_.Name -match '^\.env($|\.)|token\.json|credentials\.json|\.pem$|\.key$|\.pfx$|\.crt$' } | Select-Object FullName
Get-ChildItem -Recurse -File | Select-String -Pattern 'AKIA|AIza|ghp_|github_pat_|sk-[A-Za-z0-9]{20,}|xox[baprs]-|BEGIN (RSA|OPENSSH|PRIVATE)|DISCORD_AUTH=|TOKEN=|SECRET_KEY=|AUTH_KEY=|DATABASE_TOKEN='
```

Run tests only if they exist.
Do not claim tested runtime behavior if dependencies or secrets are missing.

## 11. Preferred Next-Step Priorities

If the user asks for improvements and does not specify priorities, prefer:

1. production safety
2. secret handling
3. deployment reliability
4. slash commands / UX improvements
5. migration from SQLite to Postgres
6. test coverage

## 12. Push Guidance

If asked to prepare for GitHub:

- verify no secrets are present
- keep `.env.example`
- keep deployment files
- stage only intended source/config files
- use `main` as the default branch

Suggested commit message style:

- `Harden deployment and add Render production config`
- `Improve Notion API error handling`
- `Add slash command support`

