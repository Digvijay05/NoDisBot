import asyncio
import discord
from discord.ext import commands
from functionality import setupBot, utils
import os
from database import SessionLocal, engine
import models
import json
import functionality.utils as utils
import functionality.security as security
import migrate

# database setup
db = SessionLocal()

migrate.run_migrations()

# prefix data
prefix = ""
prefix_data = {}

# cogs
cogs = [
    "cogs.add",
    "cogs.search",
    "cogs.delete",
    "cogs.upload",
    "cogs.help",
    "cogs.admin",
    "cogs.tasks"
]

try:
    prefix = os.environ.get("PREFIX", "*")
except Exception:
    prefix = "*"

token = os.environ.get("TOKEN")
if not token:
    print("CRITICAL: No discord TOKEN found in environment. Exiting...")
    exit(1)
    
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    print("CRITICAL: No SECRET_KEY found in environment. Exiting...")
    exit(1)

# get prefixes from the database
def fillPrefix():
    global prefix_data
    prefix_data = {}
    guilds = db.query(models.Clients).all()
    for guild in guilds:
        prefix_data[str(guild.guild_id)] = guild.prefix


# cog loading reloading
def reload_cogs():
    for cog in cogs:
        bot.reload_extension(cog)


def load_cogs():
    for cog in cogs:
        bot.load_extension(cog)


# get prefix of the guild that triggered bot
def get_prefix(client, message):
    global prefix_data
    try:
        return prefix_data[str(message.guild.id)]
    except KeyError:
        return "*"

fillPrefix()

bot = commands.Bot(command_prefix=(get_prefix), help_command=None)



# storing guild info in an attribute of bot so that all cogs can access
bot.guild_info = utils.getGuildInfo()
# loading all the cogs
load_cogs()

# Start health-check server for Render free-tier Web Service
from keep_alive import keep_alive
keep_alive()

try:
    bot.run(token)
except discord.LoginFailure:
    print("CRITICAL: Invalid discord token provided. Exiting!")
except Exception as e:
    print(f"CRITICAL: Failed to run bot -> {e}")
