"""
Bot configuration and assignee mapping service.

Provides access to environment variables and handles database mappings.
Currently single-tenant (env vars), but the interface accepts guild_id
to make call sites explicit and future-proof for multi-tenant config.
"""

import os
from dataclasses import dataclass

try:
    from Bot.database import SessionLocal
    from Bot import models
except ImportError:  # pragma: no cover - script execution fallback
    from database import SessionLocal
    import models

@dataclass
class BotConfig:
    notion_api_key: str
    notion_db_id: str
    ollama_url: str
    ollama_model: str
    
    # We can hardcode defaults for the schema property names here or expand this if needed.
    # The existing codebase checks for these when interacting with Notion.
    task_title_property: str = "Task"
    task_status_property: str = "Status"
    task_assignee_property: str = "Assignee"
    task_description_property: str = "Description"
    task_priority_property: str = "Priority"
    task_due_date_property: str = "Due Date"
    task_tags_property: str = "Tags"
    archive_mode: str = "checkbox"
    archive_status_value: str = "Done"

    def get_property_map(self):
        return {
            "title": self.task_title_property,
            "status": self.task_status_property,
            "assignee": self.task_assignee_property,
            "description": self.task_description_property,
            "priority": self.task_priority_property,
            "due_date": self.task_due_date_property,
            "tags": self.task_tags_property,
        }

def get_bot_config(guild_id=None) -> BotConfig:
    """Fetch bot configuration for a guild.

    Currently reads from environment variables (single-tenant).
    The guild_id parameter is accepted for call-site clarity and
    will be used for DB-backed per-guild config in the future.
    """
    return BotConfig(
        notion_api_key=os.environ.get("NOTION_API_KEY", ""),
        notion_db_id=os.environ.get("NOTION_DB_ID", ""),
        ollama_url=os.environ.get("OLLAMA_URL", ""),
        ollama_model=os.environ.get("OLLAMA_MODEL", "llama3"),
    )


def get_assignee_mapping(guild_id, discord_user_id):
    """Retrieve the Notion assignee value for a given Discord user."""
    db = SessionLocal()
    try:
        mapping = db.query(models.AssigneeMapping).filter(
            models.AssigneeMapping.guild_id == guild_id,
            models.AssigneeMapping.discord_user_id == str(discord_user_id)
        ).first()
        return mapping.notion_assignee_value if mapping else None
    finally:
        db.close()


def resolve_assignee_mapping(guild_id, query_str):
    """Resolve a raw mention or name string to a Notion assignee value."""
    import re
    db = SessionLocal()
    try:
        match = re.search(r'<@!?(\d+)>', query_str)
        if match:
            user_id = match.group(1)
            mapping = db.query(models.AssigneeMapping).filter(
                models.AssigneeMapping.guild_id == guild_id,
                models.AssigneeMapping.discord_user_id == user_id
            ).first()
        else:
            search_str = f"%{query_str.strip().lower()}%"
            mapping = db.query(models.AssigneeMapping).filter(
                models.AssigneeMapping.guild_id == guild_id,
                models.AssigneeMapping.discord_name.ilike(search_str)
            ).first()
            
        return mapping.notion_assignee_value if mapping else None
    finally:
        db.close()


def save_assignee_mapping(guild_id, discord_user_id, notion_value, discord_name=None):
    """Create or update a Discord-to-Notion assignee mapping.

    discord_name should be user.display_name (the server nickname or
    global display name) for stable fallback matching. Do NOT pass
    str(user) as it includes discriminator formatting that can change.
    """
    db = SessionLocal()
    try:
        mapping = db.query(models.AssigneeMapping).filter(
            models.AssigneeMapping.guild_id == guild_id,
            models.AssigneeMapping.discord_user_id == str(discord_user_id)
        ).first()
        
        if not mapping:
            mapping = models.AssigneeMapping(
                guild_id=guild_id,
                discord_user_id=str(discord_user_id),
                notion_assignee_value=notion_value,
                discord_name=discord_name
            )
            db.add(mapping)
        else:
            mapping.notion_assignee_value = notion_value
            if discord_name:
                mapping.discord_name = discord_name
                
        db.commit()
    finally:
        db.close()
