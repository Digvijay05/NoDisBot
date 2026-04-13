# Product Requirements Document

## 1. Product Name

NoDisBot: Notion Discord Bot

## 2. Purpose

NoDisBot helps Discord communities capture, organize, and retrieve resources directly from Discord while storing the source of truth in Notion.

The bot reduces the friction of:

- saving useful links shared in chat
- organizing content with tags
- searching previous resources
- uploading files into a shared knowledge base

## 3. Problem Statement

Discord servers accumulate valuable links, documents, and references, but these become difficult to find and manage over time.
Teams often want:

- a searchable resource library
- structured metadata
- low-friction capture from chat
- central storage in a collaborative tool like Notion

Without a bot, users must manually copy content from Discord into Notion, which is slow and inconsistent.

## 4. Goals

- Allow server members to save links and files from Discord into Notion
- Allow users to retrieve saved resources quickly
- Support per-server configuration
- Keep setup simple for admins
- Be reliable enough for self-hosted production use

## 5. Non-Goals

- Full Notion workspace management
- Complex analytics or dashboards
- Multi-tenant SaaS control panel
- Full moderation system
- Rich web application UI

## 6. Primary Users

- Discord server admins configuring the bot
- Community members saving and retrieving resources
- Small teams/study groups using Notion as a knowledge base

## 7. Core User Stories

### Admin

- As an admin, I want to connect my server to a Notion database so the bot can store resources.
- As an admin, I want to choose whether tags are enabled.
- As an admin, I want to change the command prefix.

### Member

- As a member, I want to save a link from Discord into Notion.
- As a member, I want to upload a file and store it in Notion.
- As a member, I want to search by title or tags.
- As a member, I want to delete a mistaken or outdated record.

## 8. Functional Requirements

### Setup

- The bot must support per-guild setup
- The bot must store a Notion API key and database ID per guild
- The bot must validate Notion credentials during setup
- The bot must support configurable prefix per guild

### Add Resource

- The bot must accept a URL and store it in Notion
- The bot should attempt to extract the page title automatically
- If title extraction fails, the bot must allow manual title entry
- The bot must detect duplicate URLs before insert
- The bot must support tags when tagging is enabled

### Search

- The bot must support search by title
- The bot must support search by tags when enabled
- The bot should return results in a readable embed

### Delete

- The bot must allow users to select a record from search results for deletion
- The bot should prefer archive/soft-delete semantics in future versions

### Upload

- The bot must accept a Discord attachment URL
- The bot must prompt for title if required
- The bot must save uploaded file references to Notion

### Help

- The bot must provide a help command based on guild configuration

## 9. Non-Functional Requirements

- Secrets must not be hardcoded
- Setup failures must be understandable
- The bot must run as a background worker
- The bot must support Dockerized deployment
- The bot should fail fast on missing required environment variables
- Logs must avoid leaking tokens or decrypted credentials

## 10. MVP Scope

- Per-guild setup
- Add URL
- Search by title
- Search by tags
- Delete resource
- Upload file reference
- Change prefix
- Docker deployment

## 11. V2 Scope

- Slash commands
- Better permission controls
- Search pagination
- Better Notion schema validation
- Archive instead of destructive delete
- Better error reporting
- Postgres-backed config storage

## 12. Success Criteria

- Admin can configure the bot in under 5 minutes
- Users can save and retrieve resources reliably
- Duplicate saves are reduced
- Search is useful enough for daily use
- Deployment is reproducible with Docker/Render

## 13. Risks

- Notion API schema mismatches
- Discord API changes
- SQLite limitations for scaling
- Weak error handling causing false-positive success responses
- Secret leakage through logs if not controlled

