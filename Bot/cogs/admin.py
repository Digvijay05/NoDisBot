import discord
from discord.ext import commands
import asyncio
from functionality import config, notion_schema


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.command(name="setup", aliases=["tasksetup"])
    async def tasksetup(self, ctx):
        """Guided setup for Notion task management."""
        guild_id = ctx.guild.id

        await ctx.send("Starting Task Bot setup. Check your DMs for the next steps.")
        
        # We will do the setup in DMs to avoid leaking API keys in the server
        try:
            dm_channel = await ctx.author.create_dm()
        except discord.Forbidden:
            await ctx.send("I cannot send you DMs. Please enable DMs from server members.")
            return

        def check(m):
            return m.author == ctx.author and m.channel == dm_channel

        async def ask_for(prompt):
            await dm_channel.send(prompt)
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=120)
                return msg.content.strip()
            except asyncio.TimeoutError:
                await dm_channel.send("Setup timed out. You took too long to respond.")
                return None

        # 1. Notion API Key
        notion_key = await ask_for("Please enter your **Notion Internal Integration Token** (e.g. `secret_...`):")
        if not notion_key: return

        # 2. Notion DB ID
        notion_db = await ask_for("Please enter your **Notion Database ID** (the 32-character string in the URL):")
        if not notion_db: return

        await dm_channel.send("Thanks. Testing Notion connection and checking database schema...")

        # Test Notion Schema
        schema_result = notion_schema.validate_schema(notion_key, notion_db)
        
        await dm_channel.send(schema_result.summary)
        
        if not schema_result.valid:
            await dm_channel.send("❌ Setup failed due to missing required properties. Please add them to your Notion database and try again.")
            return

        # 3. Ollama Settings
        ollama_url = await ask_for(
            "Please enter your **Ollama Base URL** (e.g. `http://localhost:11434` or your server's IP):\n"
            "If you want to skip and configure this later, type `skip`."
        )
        if not ollama_url: return
        
        ollama_model = None
        if ollama_url.lower() != "skip":
            ollama_model = await ask_for("Please enter the **Ollama Model Name** to use (e.g. `llama3` or `mistral`):")
            if not ollama_model: return

        # Save to DB
        save_kwargs = {
            "notion_api_key": notion_key,
            "notion_db_id": notion_db,
        }
        if ollama_url.lower() != "skip":
            save_kwargs["ollama_base_url"] = ollama_url
            save_kwargs["ollama_model"] = ollama_model

        config.save_guild_config(guild_id, **save_kwargs)

        # Also update prefix in the main bot dictionary (if used)
        if str(guild_id) in self.bot.guild_info:
            cfg = config.get_guild_config(guild_id)
            if cfg:
                self.bot.guild_info[str(guild_id)] = cfg

        await dm_channel.send("✅ Setup complete! The bot is ready to manage tasks for your server.")


    @commands.has_permissions(administrator=True)
    @commands.command(name="taskconfig")
    async def taskconfig(self, ctx):
        """Displays the current configuration."""
        guild_id = ctx.guild.id
        cfg = config.get_guild_config(guild_id)
        
        if not cfg:
            await ctx.send("Not configured yet. Please run `setup`.")
            return
            
        embed = discord.Embed(title="Task Bot Configuration", color=discord.Color.blue())
        embed.add_field(name="Bot Prefix", value=f"`{cfg.prefix}`", inline=False)
        embed.add_field(name="Notion API Key", value="Configured (hidden)", inline=False)
        embed.add_field(name="Notion Database ID", value="Configured (hidden)", inline=False)
        
        o_url = cfg.ollama_base_url if cfg.ollama_base_url else "Not set"
        o_model = cfg.ollama_model if cfg.ollama_model else "Not set"
        embed.add_field(name="Ollama URL", value=f"`{o_url}`", inline=False)
        embed.add_field(name="Ollama Model", value=f"`{o_model}`", inline=False)
        
        await ctx.send(embed=embed)


    @commands.has_permissions(administrator=True)
    @commands.command(name="mapuser")
    async def mapuser(self, ctx, user: discord.Member, *, notion_value: str):
        """Maps a Discord user to a Notion assignee value.
        Example: `*mapuser @riya Riya Sharma`
        """
        guild_id = ctx.guild.id
        config.save_assignee_mapping(guild_id, user.id, notion_value, str(user))
        
        embed = discord.Embed(
            title="User Mapped", 
            description=f"Discord user {user.mention} has been mapped to Notion assignee: **{notion_value}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Admin(bot))
