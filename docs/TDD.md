# Technical Design Document

## 1. Overview

This document describes the technical design of NoDisBot as implemented in the active `Bot/` codebase.

## 2. System Context

NoDisBot is a single-process Discord worker that:

1. receives commands from Discord
2. looks up guild configuration in local persistence
3. performs Notion API requests
4. returns command results to Discord

## 3. Runtime Components

### Entrypoint

- File: `Bot/bot.py`
- Responsibilities:
  - initialize database tables
  - load bot token and prefix
  - load guild configuration
  - register and load cogs
  - start Discord client

### Persistence Layer

- Files:
  - `Bot/database.py`
  - `Bot/models.py`
- Responsibilities:
  - configure SQLAlchemy engine/session
  - define guild configuration schema
  - persist Notion credentials and bot settings

### Command Layer

- Files:
  - `Bot/cogs/add.py`
  - `Bot/cogs/search.py`
  - `Bot/cogs/delete.py`
  - `Bot/cogs/upload.py`
  - `Bot/cogs/help.py`
- Responsibilities:
  - parse command input
  - validate guild setup
  - call helper logic
  - send Discord embeds/responses

### Business Logic Layer

- Files under `Bot/functionality/`
- Responsibilities:
  - setup conversations
  - Notion API calls
  - title extraction
  - duplicate detection
  - encryption/decryption helpers
  - tag parsing and search payload construction

## 4. Data Model

Current model:

- `Clients`
  - `guild_id`
  - `notion_api_key`
  - `notion_db_id`
  - `tag`
  - `prefix`

The active design stores guild-level configuration locally and uses Notion as the primary data store for resource records.

## 5. Storage Design

### Current

- SQLAlchemy + SQLite
- Default path derived from `DATA_DIR`
- Optional override through `DATABASE_URL`

### Intended Production Use

- SQLite acceptable for low-scale single worker deployments
- Postgres recommended for more robust production usage

## 6. External Integrations

### Discord

- Library: `discord.py`
- Role:
  - receive commands
  - send embeds
  - support interactive text-based setup and follow-up prompts

### Notion API

- Role:
  - validate database access
  - create records
  - query records
  - patch records for delete/update behavior

## 7. Command Flows

### Setup Flow

1. User runs setup command
2. Bot prompts for Notion API key
3. Bot prompts for database ID
4. Bot prompts for tag enablement
5. Bot verifies database access
6. Bot encrypts and stores guild settings

### Add Flow

1. User submits URL
2. Bot validates URL
3. Bot extracts title or asks for one
4. Bot checks duplicates
5. Bot writes record to Notion
6. Bot confirms success/failure

### Search Flow

1. User submits title or tags
2. Bot determines search mode
3. Bot queries Notion
4. Bot formats results into embeds

### Delete Flow

1. User submits title or tags
2. Bot searches records
3. Bot prompts user to choose a result
4. Bot patches selected record
5. Bot confirms result

### Upload Flow

1. User uploads attachment with command
2. Bot reads attachment URL
3. Bot asks for title
4. Bot writes record to Notion

## 8. Deployment Design

### Current standard

- Dockerized worker
- Render `worker` service
- persistent disk mounted at `/app/data`
- startup validation script checks required env vars

### Key environment variables

- `TOKEN`
- `SECRET_KEY`
- `PREFIX`
- `DATA_DIR`
- `DATABASE_URL`

## 9. Security Design

### Current measures

- Notion credentials are encrypted before persistence
- required secrets are environment-based
- container runs as non-root

### Gaps

- some code paths still log sensitive operational details
- broad exception handling reduces observability and safety
- no robust permission/role model for admin commands

## 10. Operational Constraints

- no HTTP server
- no queue system
- no cache layer
- no automated migration framework
- minimal test coverage

## 11. Technical Debt

- legacy `v1/` code remains in repo
- broad `except:` usage
- incomplete error propagation from Notion API
- SQLite persistence is not ideal for scaling
- command UX should move to slash commands and modals

## 12. Recommended Evolution

1. add structured logging without secrets
2. improve Notion API error handling
3. add request timeouts and retries
4. add tests for setup/add/search/delete flows
5. migrate guild config storage to Postgres
6. adopt slash commands and interactive components

