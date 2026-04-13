# ⚠️ Deprecated — Legacy v1 Code

This directory contains the **original v1 implementation** of the NoDisBot Discord bot.

**Do not use this code.** It is retained for historical reference only.

## Why it's deprecated

- Relies on direct Notion API calls with no abstraction layer
- Google Drive integration uses insecure patterns (`os.system("wget ...")`, `os.system("rm ...")`)
- No input validation or error handling beyond bare `try/except`
- No encryption, no database abstraction, no structured configuration

## Current implementation

The active, production-ready bot lives in [`/Bot`](../Bot/). See the root [README.md](../README.md) and [SETUP.md](../SETUP.md) for usage.
