# Task Bot Technical Specification

This document tells an implementation agent exactly how to evolve the current bot into the task-management version.

## 1. Implementation Goal

Refactor the active `Bot/` codebase so the main workflow is task management through Discord, Ollama, and Notion.

The coding agent should preserve the current repo style where practical, but it may introduce clearer modules if needed.

## 2. High-Level Architecture

The implementation should introduce these logical modules:

### Discord Command Layer

- task setup/config commands
- task create/update/search/archive commands
- preview/confirmation flow

Suggested location:

- `Bot/cogs/tasks.py`
- `Bot/cogs/admin.py`

### Configuration Layer

- guild config persistence
- Ollama settings persistence
- property mapping persistence
- assignee mapping persistence

Suggested location:

- `Bot/models.py`
- `Bot/functionality/config.py`

### LLM Parsing Layer

- prompt generation
- Ollama HTTP client
- structured parsing contract
- fallback/error handling

Suggested location:

- `Bot/functionality/ollama_client.py`
- `Bot/functionality/task_parser.py`

### Notion Task Layer

- validate database schema
- create task
- update task
- search task
- archive task
- map internal fields to Notion properties

Suggested location:

- `Bot/functionality/notion_tasks.py`
- `Bot/functionality/notion_schema.py`

### Task Resolution Layer

- identify target task for updates
- resolve assignee names
- normalize statuses
- normalize priorities
- normalize dates

Suggested location:

- `Bot/functionality/task_resolution.py`

## 3. Data Model Changes

The current `Clients` model is insufficient for the target product.

The coding agent should extend or replace it with fields such as:

- `guild_id`
- `notion_api_key`
- `notion_db_id`
- `prefix`
- `ollama_base_url`
- `ollama_model`
- `task_title_property`
- `task_status_property`
- `task_assignee_property`
- `task_description_property`
- `task_priority_property`
- `task_due_date_property`
- `task_tags_property`
- `archive_mode`

Additionally create an assignee mapping table if persistence remains relational:

- `guild_id`
- `discord_user_id`
- `discord_name`
- `notion_assignee_value`

If the agent chooses to defer schema migration complexity, it must document the compromise clearly.

## 4. Required Commands

The implementation should support these commands first.

### Admin commands

- `setup`
  - configure Notion DB
  - configure Ollama base URL
  - configure model
  - validate schema

- `mapuser`
  - map a Discord user/name to a Notion assignee value

- `config`
  - show current guild configuration

### Task commands

- `task create <natural language>`
- `task update <natural language>`
- `task move <task> <status>`
- `task assign <task> <person>`
- `task show mine`
- `task show status <status>`
- `task search <query>`
- `task archive <task>`
- `task help`

If the agent retains prefix commands for MVP, that is acceptable.
Slash commands can be deferred to V2.

## 5. Internal Task Schema

The bot should convert natural language into a normalized internal schema before touching Notion.

Suggested internal task object:

```json
{
  "title": "Auth API integration",
  "description": "Complete backend integration for auth flows",
  "status": "To Do",
  "assignee": "Riya",
  "due_date": "2026-04-17",
  "priority": "High",
  "tags": ["backend", "auth"],
  "project": "Platform",
  "confidence": 0.92,
  "needs_confirmation": true
}
```

Rules:

- normalize status into canonical values
- return ISO date strings where possible
- include confidence if the LLM can provide it
- require confirmation before writes

## 6. Ollama Integration Contract

The bot should call Ollama over HTTP.

The coding agent should implement:

- configurable base URL
- configurable model
- request timeout
- strict structured output expectation
- robust failure handling

The parser should request JSON output only.
Do not parse free-form prose if avoidable.

### Required parser intents

- create task
- update task
- move task
- assign task
- archive task
- search task

The prompt should clearly ask the model to:

- identify user intent
- extract fields
- identify ambiguities
- avoid inventing missing facts

## 7. Notion Integration Rules

The current repository already has Notion request logic, but it is resource-oriented.
The coding agent should not reuse the old payload shape blindly.

Implement task-specific behavior:

- create task rows
- update existing task rows
- query tasks by title/status/assignee
- archive tasks safely
- validate database schema during setup

Avoid:

- hardcoded property names where configurable mapping is possible
- clearing fields as a substitute for proper archival unless schema forces it

## 8. Confirmation Flow

Natural-language write operations must be previewed before execution.

Suggested flow:

1. user enters natural-language request
2. bot calls Ollama
3. bot shows structured preview
4. user confirms or cancels
5. bot writes to Notion

If ambiguity remains:

- ask a focused follow-up question
- do not guess silently

## 9. Search and Resolution Strategy

Task updates need safe task identification.

The agent should implement:

- exact title match if possible
- close match search fallback
- numbered selection if multiple candidates exist
- assignee filtering when available
- status filtering when useful

Do not update the wrong task silently.

## 10. MVP Milestones

### Milestone 1: Data and Setup Foundation

- extend guild config model
- store Ollama settings
- add Notion schema validation
- add env validation where needed

### Milestone 2: Ollama Parser

- add HTTP client
- add prompt template
- add strict JSON parsing
- add error handling and timeout handling

### Milestone 3: Task CRUD Core

- create task in Notion
- update task in Notion
- search/list tasks
- archive task

### Milestone 4: Discord UX

- add task commands
- add preview and confirmation flow
- add assignee mapping commands

### Milestone 5: Reliability

- add tests for parser/output normalization
- add tests for task payload generation
- add tests for safe task resolution

## 11. Security and Reliability Requirements

The coding agent must follow these rules:

- never log secrets or decrypted credentials
- add timeouts to all outbound HTTP requests
- validate Ollama and Notion config before use
- fail clearly on invalid setup
- avoid broad `except:` in new code
- preserve non-root container behavior

## 12. Testing Requirements

Minimum tests to add:

- parser output normalization
- status normalization
- date normalization
- assignee mapping behavior
- Notion payload generation
- command preview flow logic

Mock external services:

- Ollama API
- Notion API

## 13. Migration Guidance

The current codebase has resource-management logic.
The coding agent should:

- preserve existing deployability
- avoid breaking basic startup
- either replace old cogs cleanly or add new task-specific cogs
- document any deprecated commands

If old commands remain temporarily, mark them as legacy.

