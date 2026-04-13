import os
import discord
from discord.ext import commands
from database import SessionLocal
import models
import migrate

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

ollama_url = os.environ.get("OLLAMA_URL")
if not ollama_url:
    print("CRITICAL: No OLLAMA_URL found in environment. Exiting...")
    exit(1)

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
    from keep_alive import keep_alive
    keep_alive()
except ImportError:
    pass

try:
    bot.run(token)
except discord.LoginFailure:
    print("CRITICAL: Invalid discord token provided. Exiting!")
except Exception as e:
    print(f"CRITICAL: Failed to run bot -> {e}")
