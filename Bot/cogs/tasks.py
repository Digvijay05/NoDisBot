import asyncio
import discord
from discord.ext import commands

from functionality.config import get_bot_config, save_assignee_mapping, resolve_assignee_mapping
from functionality.notion_schema import async_validate_schema
from functionality.notion_tasks import create_task, update_task, search_tasks, archive_task
from functionality.task_parser import parse_task_request
from functionality.task_resolution import resolve_task_candidates


def _extract_property_value(task: dict, internal_key: str, resolved_schema: dict) -> str:
    """Extract a human-readable current value from a Notion task's properties.

    Used to build before/after diffs for update confirmations.
    """
    props = task.get("properties", {})
    schema_entry = resolved_schema.get(internal_key)
    if not schema_entry:
        return None

    notion_name = schema_entry["name"]
    prop = props.get(notion_name)
    if not prop:
        return None

    ptype = prop.get("type", "")

    if ptype == "title":
        arr = prop.get("title", [])
        return arr[0].get("text", {}).get("content", "") if arr else ""

    elif ptype == "rich_text":
        arr = prop.get("rich_text", [])
        return arr[0].get("text", {}).get("content", "") if arr else ""

    elif ptype == "status":
        s = prop.get("status")
        return s.get("name", "") if s else ""

    elif ptype == "select":
        s = prop.get("select")
        return s.get("name", "") if s else ""

    elif ptype == "multi_select":
        items = prop.get("multi_select", [])
        return ", ".join(i.get("name", "") for i in items) if items else ""

    elif ptype == "date":
        d = prop.get("date")
        return d.get("start", "") if d else ""

    elif ptype == "people":
        people = prop.get("people", [])
        return ", ".join(p.get("name", p.get("id", "")) for p in people) if people else ""

    elif ptype == "checkbox":
        return str(prop.get("checkbox", False))

    return str(prop) if prop else None


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _confirm_action(self, ctx, prompt_text: str, timeout: int = 30) -> bool:
        """Text-based confirmation flow tailored for MVP safety in multi-user channels."""
        msg = await ctx.send(f"{prompt_text}\n\n*Type **confirm** to proceed, or **cancel** to abort.*")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["confirm", "cancel"]
            
        try:
            reply = await self.bot.wait_for("message", check=check, timeout=timeout)
            if reply.content.lower() == "confirm":
                return True
            else:
                await ctx.send("Action cancelled.")
                return False
        except asyncio.TimeoutError:
            await ctx.send("Action timed out. Cancelled.")
            return False

    async def _select_from_candidates(self, ctx, candidates: list, prompt_text: str, timeout: int = 45) -> dict:
        """Prompt user to select from ambiguous candidates."""
        lines = [prompt_text]
        for idx, c in enumerate(candidates, 1):
            props = c.get("properties", {})
            # Attempt to extract title safely, assuming 'title' is the property type
            title = "Unknown Task"
            for k, v in props.items():
                if v.get("type") == "title":
                    title_arr = v.get("title", [])
                    if title_arr:
                        title = title_arr[0].get("text", {}).get("content", "Unknown Task")
                    break
            
            url = c.get("url", "")
            lines.append(f"**{idx}.** {title} ([Link]({url}))")
            
        lines.append("\n*Type the number of the task you meant, or **cancel** to abort.*")
        
        await ctx.send("\n".join(lines))
        
        def check(m):
            if m.author != ctx.author or m.channel != ctx.channel:
                return False
            content = m.content.lower()
            if content == "cancel":
                return True
            return content.isdigit() and 1 <= int(content) <= len(candidates)
            
        try:
            reply = await self.bot.wait_for("message", check=check, timeout=timeout)
            if reply.content.lower() == "cancel":
                await ctx.send("Selection cancelled.")
                return None
            idx = int(reply.content) - 1
            return candidates[idx]
        except asyncio.TimeoutError:
            await ctx.send("Selection timed out.")
            return None


    @commands.command(name="task", aliases=["t"])
    async def natural_task(self, ctx, *, query: str = None):
        if not query:
            return await ctx.send("Please provide a task instruction. Example: `!task assign the auth api ticket to Riya`")
            
        config = get_bot_config(ctx.guild.id)
        
        if not config or not config.notion_api_key or not config.ollama_url:
            return await ctx.send("This server hasn't been configured with API keys. Please check your .env file.")
            
        api_key = config.notion_api_key
        
        # We need the property map to do Notion things safely
        prop_map = config.get_property_map()

        # Async + cached schema validation — never blocks the event loop
        async with ctx.typing():
            schema_res = await async_validate_schema(api_key, config.notion_db_id, prop_map)
            
        if not schema_res.valid:
            return await ctx.send(f"Your Notion database schema is invalid or missing properties:\n{schema_res.summary}")
            
        resolved_schema = schema_res.resolved_schema
        
        async with ctx.typing():
            parsed_data, err = await parse_task_request(query, config.ollama_url, config.ollama_model)
            
        if err:
            return await ctx.send(f"Error parsing task: {err}")
            
        action = parsed_data.get("action", "create").lower()
        task_data = parsed_data.get("task", {})
        
        # Assignee mapping — resolve Discord mentions/names to Notion values
        if "assignee" in task_data and task_data["assignee"]:
            mapped_value = resolve_assignee_mapping(ctx.guild.id, task_data["assignee"])
            if mapped_value:
                task_data["assignee"] = mapped_value
        
        if action == "create":
            await self._handle_create(ctx, api_key, config.notion_db_id, task_data, resolved_schema)
        elif action in ["update", "move", "assign"]:
            await self._handle_update(ctx, api_key, config.notion_db_id, task_data, resolved_schema, action)
        elif action == "archive":
            await self._handle_archive(ctx, api_key, config.notion_db_id, task_data, resolved_schema, config)
        elif action == "search":
            await self._handle_search(ctx, api_key, config.notion_db_id, task_data, resolved_schema)
        else:
            await ctx.send(f"Unsupported action extracted: `{action}`. Try rephrasing.")

    async def _handle_create(self, ctx, api_key, db_id, task_data, resolved_schema):
        title = task_data.get("title", "Untitled Task")
        
        # Preview Embed
        embed = discord.Embed(title="Create New Task", color=discord.Color.blue())
        for k, v in task_data.items():
            if v:
                embed.add_field(name=k.capitalize(), value=str(v), inline=False)
                
        await ctx.send(embed=embed)
        
        if not await self._confirm_action(ctx, "Does this look correct?"):
            return
            
        async with ctx.typing():
            res = await create_task(api_key, db_id, task_data, resolved_schema)
            
        if res["ok"]:
            page_url = res["data"].get("url", "")
            await ctx.send(f"Success: Task created!\n{page_url}")
        else:
            await ctx.send(f"Error: Failed to create task:\n`{res.get('message')}`")

    async def _handle_update(self, ctx, api_key, db_id, task_data, resolved_schema, action):
        title_query = task_data.get("title")
        if not title_query:
            return await ctx.send(f"I couldn't determine which task to {action}. Please include the task title.")
            
        # Build search filters from all safe narrowing fields (F3)
        search_filters = {"title": title_query}
        for field in ("status", "assignee", "priority"):
            if task_data.get(field):
                search_filters[field] = task_data[field]

        async with ctx.typing():
            search_res = await search_tasks(api_key, db_id, search_filters, resolved_schema)
            
        if not search_res["ok"]:
            return await ctx.send(f"Error: Search failed:\n`{search_res.get('message')}`")
            
        results = search_res.get("results", [])
        
        status_res, result = resolve_task_candidates(results, title_query)
        
        target_task = None
        if status_res == "no_match":
            return await ctx.send(f"Could not find any tasks matching '{title_query}'.")
        elif status_res == "resolved":
            target_task = result
        elif status_res == "ambiguous":
            target_task = await self._select_from_candidates(ctx, result[:5], f"Found {len(result)} potential tasks. Which one did you mean?")
            
        if not target_task:
            return
            
        # Do not overwrite the title unless explicitly told to in a pure update command,
        # usually they are just referencing the title. We strip title from update payload
        # unless it's a rename operation, but it's hard to distinguish naturally. 
        # For safety on assignment/moves, we pop the title.
        update_payload = dict(task_data)
        if action in ["move", "assign", "archive"] and "title" in update_payload:
            update_payload.pop("title")

        # True diff preview: show current vs new values (F4)
        embed = discord.Embed(title=f"Confirm {action.capitalize()}", description="Proposed changes:", color=discord.Color.orange())
        has_changes = False
        for key, new_val in update_payload.items():
            if not new_val:
                continue
            current_val = _extract_property_value(target_task, key, resolved_schema)
            if current_val is not None and current_val != str(new_val):
                embed.add_field(name=key.capitalize(), value=f"`{current_val}` -> `{new_val}`", inline=False)
                has_changes = True
            elif current_val is None:
                embed.add_field(name=key.capitalize(), value=f"(not set) -> `{new_val}`", inline=False)
                has_changes = True

        if not has_changes:
            return await ctx.send("No changes detected between current values and proposed update.")

        await ctx.send(embed=embed)
        
        if not await self._confirm_action(ctx, "Proceed with update?"):
            return
            
        async with ctx.typing():
            res = await update_task(api_key, target_task["id"], update_payload, resolved_schema)
            
        if res["ok"]:
            await ctx.send(f"Success: Task updated!\n{res['data'].get('url')}")
        else:
            await ctx.send(f"Error: Failed to update task:\n`{res.get('message')}`")

    async def _handle_archive(self, ctx, api_key, db_id, task_data, resolved_schema, config):
        title_query = task_data.get("title")
        if not title_query:
            return await ctx.send("I couldn't determine which task to archive. Please include the task title.")

        # Build search filters from all safe narrowing fields (F3)
        search_filters = {"title": title_query}
        for field in ("status", "assignee", "priority"):
            if task_data.get(field):
                search_filters[field] = task_data[field]

        async with ctx.typing():
            search_res = await search_tasks(api_key, db_id, search_filters, resolved_schema)
            
        if not search_res["ok"]:
            return await ctx.send(f"Error: Search failed:\n`{search_res.get('message')}`")
            
        results = search_res.get("results", [])
        
        status_res, result = resolve_task_candidates(results, title_query)
        
        target_task = None
        if status_res == "no_match":
            return await ctx.send(f"Could not find any tasks matching '{title_query}'.")
        elif status_res == "resolved":
            target_task = result
        elif status_res == "ambiguous":
            target_task = await self._select_from_candidates(ctx, result[:5], f"Found {len(result)} potential tasks. Which one did you mean?")
            
        if not target_task:
            return
            
        if not await self._confirm_action(ctx, f"Are you sure you want to archive this task?"):
             return
             
        async with ctx.typing():
            res = await archive_task(api_key, target_task["id"], resolved_schema, config.archive_mode, config.archive_status_value)
            
        if res["ok"]:
            await ctx.send("Success: Task archived!")
        else:
            await ctx.send(f"Error: Failed to archive task:\n`{res.get('message')}`")

    async def _handle_search(self, ctx, api_key, db_id, task_data, resolved_schema):
         async with ctx.typing():
             # Build search filters intelligently
             filters = {}
             if task_data.get("title"):
                 filters["title"] = task_data["title"]
             if task_data.get("status"):
                 filters["status"] = task_data["status"]
             if task_data.get("priority"):
                 filters["priority"] = task_data["priority"]
                 
             search_res = await search_tasks(api_key, db_id, filters, resolved_schema)
             
         if not search_res["ok"]:
             return await ctx.send(f"Error: Search failed:\n`{search_res.get('message')}`")
             
         results = search_res.get("results", [])
         if not results:
             return await ctx.send("No tasks match your search criteria.")
             
         embed = discord.Embed(title=f"Search Results ({len(results)})", color=discord.Color.green())
         for idx, r in enumerate(results[:5], 1):
             props = r.get("properties", {})
             title = "Unknown Task"
             for k, v in props.items():
                 if v.get("type") == "title":
                     title_arr = v.get("title", [])
                     if title_arr:
                         title = title_arr[0].get("text", {}).get("content", "Unknown Task")
                     break
             url = r.get("url", "")
             embed.add_field(name=f"{idx}. {title}", value=f"[Link]({url})", inline=False)
             
         if len(results) > 5:
             embed.set_footer(text=f"Showing top 5 of {len(results)} results")
             
         await ctx.send(embed=embed)

    @commands.has_permissions(administrator=True)
    @commands.command(name="mapuser")
    async def mapuser(self, ctx, user: discord.Member, *, notion_value: str):
        """Maps a Discord user to a Notion assignee value.
        Example: `!mapuser @riya Riya Sharma`
        """
        guild_id = ctx.guild.id
        save_assignee_mapping(guild_id, user.id, notion_value, user.display_name)
        
        embed = discord.Embed(
            title="User Mapped", 
            description=f"Discord user {user.mention} has been mapped to Notion assignee: **{notion_value}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Tasks(bot))
