"""
Guild configuration and assignee mapping service.
Provides access to database models and handles secret encryption/decryption.
"""

from database import SessionLocal
import models
from functionality import security


def get_guild_config(guild_id):
    """Fetch the Clients config for a guild.
    
    API keys and DB IDs are returned decrypted if present.
    """
    db = SessionLocal()
    try:
        guild = db.query(models.Clients).filter(models.Clients.guild_id == guild_id).first()
        if not guild:
            return None
        
        # We don't want to modify the DB object in-place and accidentally commit decrypted
        # values, so we create a detached copy for the caller.
        return models.Clients(
            guild_id=guild.guild_id,
            notion_api_key=security.getKey(guild.notion_api_key) if guild.notion_api_key else None,
            notion_db_id=security.getKey(guild.notion_db_id) if guild.notion_db_id else None,
            tag=guild.tag,
            prefix=guild.prefix,
            ollama_base_url=guild.ollama_base_url,
            ollama_model=guild.ollama_model,
            task_title_property=guild.task_title_property,
            task_status_property=guild.task_status_property,
            task_assignee_property=guild.task_assignee_property,
            task_description_property=guild.task_description_property,
            task_priority_property=guild.task_priority_property,
            task_due_date_property=guild.task_due_date_property,
            task_tags_property=guild.task_tags_property,
            archive_mode=guild.archive_mode,
        )
    finally:
        db.close()


def save_guild_config(guild_id, **kwargs):
    """Create or update guild config.
    
    If notion_api_key or notion_db_id are provided in kwargs,
    they will be encrypted before saving.
    """
    db = SessionLocal()
    try:
        guild = db.query(models.Clients).filter(models.Clients.guild_id == guild_id).first()
        
        # Encrypt secrets if they were provided
        raw_api_key = kwargs.get("notion_api_key")
        raw_db_id = kwargs.get("notion_db_id")
        
        if raw_api_key is not None:
            kwargs["notion_api_key"] = security.encrypt(raw_api_key)
        if raw_db_id is not None:
            kwargs["notion_db_id"] = security.encrypt(raw_db_id)
            
        if not guild:
            # Pop keys if we don't have them but need to satisfy __init__ defaults? 
            # Actually, the models.Clients init expects positional args.
            
            # Fetch default values for what's missing so we can construct models.Clients properly.
            # Using kwargs or defaults.
            new_client = models.Clients(
                guild_id=guild_id,
                notion_api_key=kwargs.get("notion_api_key", ""),
                notion_db_id=kwargs.get("notion_db_id", ""),
            )
            for k, v in kwargs.items():
                if hasattr(new_client, k):
                    setattr(new_client, k, v)
            db.add(new_client)
        else:
            for k, v in kwargs.items():
                if hasattr(guild, k):
                    setattr(guild, k, v)
                    
        db.commit()
    finally:
        db.close()


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
    """Create or update a Discord-to-Notion assignee mapping."""
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
