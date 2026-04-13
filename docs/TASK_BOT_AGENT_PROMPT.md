# Task Bot Agent Prompt

Use this prompt when assigning implementation work to an AI coding agent.

```text
Implement the task-management evolution of this repository using the docs in `docs/`.

Primary references:
- `docs/TASK_BOT_PRD.md`
- `docs/TASK_BOT_TECH_SPEC.md`
- `docs/TASK_BOT_IMPLEMENTATION_ROADMAP.md`
- `AGENTS.md`
- `docs/RUNBOOK.md`

Goal:
Turn the active `Bot/` application from a resource-saving Notion Discord bot into a Discord-to-Notion task bot powered by Ollama for natural-language task parsing.

Constraints:
- Work only in the active `Bot/` code unless legacy compatibility is explicitly needed
- Treat `v1/` as legacy reference-only
- Preserve Docker/Render deployability
- Keep the bot as a background worker, not a web app
- Never hardcode secrets
- Never log decrypted credentials or tokens
- Add timeouts for outbound HTTP calls
- Avoid broad `except:` in new or modified logic
- Use confirmation before natural-language write operations

MVP features to implement:
- setup/config for Notion + Ollama
- natural-language task creation
- natural-language task updates
- task move/assign/list/search/archive flows
- assignee mapping
- preview/confirmation before writes

Required engineering outcomes:
- normalized internal task schema
- Ollama client with structured JSON parsing
- Notion task service with schema validation
- tests for parser normalization and Notion payload generation

Execution order:
1. data/config foundation
2. Ollama parser layer
3. Notion task service
4. Discord task commands
5. assignee mapping
6. reliability hardening
7. tests

Do not stop at analysis. Implement end-to-end unless blocked by a truly missing product decision.
If blocked, make the safest reasonable assumption and document it clearly.
```

