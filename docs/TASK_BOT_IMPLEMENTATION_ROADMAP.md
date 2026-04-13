# Task Bot Implementation Roadmap

This roadmap is written for an implementation agent.
Work in order unless the user explicitly reprioritizes.

## Phase 1: Foundation

### Goals

- keep the bot runnable
- prepare config and data model for task workflow
- avoid breaking deployment

### Tasks

- review current `Bot/` command and helper structure
- extend the guild config model to support Ollama and task property mappings
- keep `Bot/database.py` compatible with `DATA_DIR` and `DATABASE_URL`
- add migration logic or safe fallback handling for existing local DBs
- create a task-focused setup flow

### Deliverables

- updated models
- updated setup/config flow
- schema validation against Notion task database

## Phase 2: Ollama Parsing Layer

### Goals

- turn natural language into structured task data safely

### Tasks

- implement `ollama_client.py`
- implement timeout handling
- implement prompt template for task extraction
- require JSON-only output
- validate and normalize parsed fields

### Deliverables

- reusable Ollama client
- parser service returning normalized task objects
- unit tests for parser normalization

## Phase 3: Notion Task Service

### Goals

- create/update/search/archive tasks in Notion

### Tasks

- implement Notion schema validation
- implement task creation payload builder
- implement task update payload builder
- implement task search by title/status/assignee
- implement archive strategy

### Deliverables

- `notion_tasks.py`
- `notion_schema.py`
- test coverage for payload mapping

## Phase 4: Discord Task Commands

### Goals

- expose the task workflow to Discord users clearly

### Tasks

- add task creation command
- add task update command
- add task move command
- add task assign command
- add list/search commands
- add archive command
- add confirmation/cancel flow

### Deliverables

- new cogs for task/admin commands
- updated help output
- safer user interaction flow

## Phase 5: Assignee Mapping

### Goals

- make Discord identity usable in Notion assignment

### Tasks

- add persistent assignee mapping model or config
- add admin command for mapping users
- resolve Discord mentions/usernames to Notion assignee values
- handle missing mappings gracefully

### Deliverables

- mapping persistence
- mapping commands
- assignee resolution logic

## Phase 6: Reliability and Hardening

### Goals

- make the task bot dependable in production

### Tasks

- remove or replace broad `except:` in touched paths
- add timeouts to outbound HTTP requests
- improve user-facing Notion/Ollama error messages
- avoid sensitive logging
- add startup/config validation where appropriate

### Deliverables

- improved error handling
- safer logs
- better operational stability

## Phase 7: Test Coverage

### Goals

- increase confidence before further feature growth

### Tasks

- add parser tests
- add mapping tests
- add Notion payload tests
- add task resolution tests
- add command-flow tests where practical

### Deliverables

- `tests/` directory
- CI-friendly tests

## Phase 8: V2 Enhancements

### Goals

- improve UX and scale capabilities

### Tasks

- migrate to slash commands
- add reminders/digests
- add subtasks
- add improved search filters
- evaluate Postgres migration for guild config

### Deliverables

- improved UX
- stronger production posture

## Definition of Done for MVP

MVP is complete when all of the following are true:

- admin can configure Notion and Ollama
- bot can parse a natural-language task create request
- bot previews parsed task fields
- bot creates task in Notion after confirmation
- bot can update task fields
- bot can move tasks across core statuses
- bot can assign tasks
- bot can list/search tasks
- bot can archive tasks safely
- tests exist for critical parser and payload logic

