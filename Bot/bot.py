import os
import discord
from discord.ext import commands

try:
    from Bot.database import SessionLocal
    from Bot import models, migrate
except ImportError:  # pragma: no cover - script execution fallback
    from database import SessionLocal
    import models
    import migrate

try:
    from Bot.functionality.config import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL
except ImportError:  # pragma: no cover - script execution fallback
    from functionality.config import DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_URL

# database setup
db = SessionLocal()

migrate.run_migrations()

# Required integrations fail-fast 
token = os.environ.get("TOKEN")
if not token:
    print("CRITICAL: No discord TOKEN found in environment. Exiting...")
    exit(1)

notion_api_key = os.environ.get("NOTION_API_KEY")
if not notion_api_key:
    print("CRITICAL: No NOTION_API_KEY found in environment. Exiting...")
    exit(1)

notion_db_id = os.environ.get("NOTION_DB_ID")
if not notion_db_id:
    print("CRITICAL: No NOTION_DB_ID found in environment. Exiting...")
    exit(1)

ollama_api_key = os.environ.get("OLLAMA_API") or os.environ.get("OLLAMA_API_KEY")
if not ollama_api_key:
    print("CRITICAL: No OLLAMA_API found in environment. Exiting...")
    exit(1)

os.environ.setdefault("OLLAMA_URL", DEFAULT_OLLAMA_URL)
os.environ.setdefault("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
os.environ.setdefault("OLLAMA_API_KEY", ollama_api_key)

# cogs
cogs = [
    "cogs.tasks"
]

# cog loading reloading
def load_cogs():
    for cog in cogs:
        bot.load_extension(cog)

COMMAND_PREFIX = "!"

def get_prefix(client, message):
    return COMMAND_PREFIX

bot = commands.Bot(command_prefix=get_prefix, help_command=None)

# loading all the cogs
load_cogs()

# Start health-check server for Render free-tier Web Service
try:
    from Bot.keep_alive import keep_alive
except ImportError:
    try:
        from keep_alive import keep_alive
    except ImportError:
        keep_alive = None

if keep_alive:
    keep_alive()

try:
    bot.run(token)
except discord.LoginFailure:
    print("CRITICAL: Invalid discord token provided. Exiting!")
except Exception as e:
    print(f"CRITICAL: Failed to run bot -> {e}")
