# Task Bot PRD

## 1. Product Direction

NoDisBot should evolve from a generic Notion resource bot into a Discord-to-Notion task management bot.

The new primary use case is:

- users describe tasks in natural language in Discord
- the bot calls an Ollama-hosted LLM
- the LLM converts the input into structured task data
- the bot creates, updates, searches, moves, and archives tasks in Notion

## 2. Target Outcome

The bot should let a Discord team manage a Notion task board using plain English, with minimal manual formatting.

Example:

- User: `Create a task for Riya to finish auth API integration by Friday and put it in to do`
- Bot:
  - extracts title, assignee, due date, status
  - shows preview
  - writes task to Notion after confirmation

## 3. Core Jobs To Be Done

- Capture tasks quickly from Discord chat
- Structure messy natural language into clean Notion task records
- Keep statuses consistent across backlog, to-do, in progress, and done
- Assign work clearly to people
- Let users update tasks without opening Notion manually

## 4. Primary Users

- Server admins
- Team leads
- Contributors who create or update tasks from Discord

## 5. MVP Scope

### Admin Setup

- Configure Notion task database per Discord guild
- Configure Ollama base URL per guild or globally
- Configure Ollama model name per guild or globally
- Validate that the Notion database contains required properties
- Configure default command prefix

### Task Create

- Natural-language task creation
- Extract these fields:
  - title
  - description
  - status
  - assignee
  - due date
  - priority
  - tags or project
- Show preview before write
- Confirm or cancel

### Task Update

- Natural-language updates
- Support updating:
  - title
  - description
  - assignee
  - status
  - due date
  - priority
  - tags/project

### Status Management

- Allowed statuses:
  - Backlog
  - To Do
  - In Progress
  - Done

### Search and List

- Show my tasks
- Show tasks by status
- Search by keyword/title
- Show tasks assigned to a specific person

### Archive

- Archive task instead of hard delete

### Permissions

- Admin-only setup/config commands
- Optional admin restriction for archive/delete commands

## 6. V2 Scope

- Slash commands and modals
- Better assignee resolution
- Multiple task databases or project boards
- Reminder and digest system
- Bulk update operations
- Subtasks
- Audit log
- Improved ambiguity handling

## 7. Non-Goals

- Full project management suite
- Sprint planning
- Story points
- Workload charts
- Autonomous edits without confirmation
- Rich web dashboard

## 8. Required Notion Properties

The target Notion database should support at minimum:

- `Task` or `Title` as title property
- `Status` as select or status property
- `Assignee` as people, rich text, or select
- `Description` as rich text
- `Priority` as select
- `Due Date` as date
- `Tags` or `Project` as multi-select/select
- `Archived` as checkbox or status-driven archive strategy

The implementation should support configurable property mapping instead of hardcoding names forever.

## 9. Product Safety Rules

- Never write to Notion without user confirmation for natural-language parsing flows
- Never hard delete by default
- Never log tokens or decrypted credentials
- Never assume an assignee match without confidence handling
- Never assume date parsing without previewing ambiguous dates

