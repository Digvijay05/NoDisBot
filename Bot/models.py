import os
from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.sqltypes import Boolean
from database import Base

PREFIX = os.environ.get("PREFIX", "*")


class Clients(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, index=True, nullable=False)
    notion_api_key = Column(String, nullable=False)
    notion_db_id = Column(String, nullable=False)
    tag = Column(Boolean, default=False)
    prefix = Column(String, default=PREFIX)

    # --- Ollama settings (per-guild) ---
    ollama_base_url = Column(String, nullable=True)
    ollama_model = Column(String, nullable=True)

    # --- Notion task property mappings ---
    task_title_property = Column(String, default="Task")
    task_status_property = Column(String, default="Status")
    task_assignee_property = Column(String, default="Assignee")
    task_description_property = Column(String, default="Description")
    task_priority_property = Column(String, default="Priority")
    task_due_date_property = Column(String, default="Due Date")
    task_tags_property = Column(String, default="Tags")

    # --- Archive strategy ---
    archive_mode = Column(String, default="checkbox")

    def __init__(
        self,
        guild_id,
        notion_api_key,
        notion_db_id,
        tag=False,
        prefix=PREFIX,
        ollama_base_url=None,
        ollama_model=None,
        task_title_property="Task",
        task_status_property="Status",
        task_assignee_property="Assignee",
        task_description_property="Description",
        task_priority_property="Priority",
        task_due_date_property="Due Date",
        task_tags_property="Tags",
        archive_mode="checkbox",
    ):
        self.guild_id = guild_id
        self.notion_api_key = notion_api_key
        self.notion_db_id = notion_db_id
        self.tag = tag
        self.prefix = prefix
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.task_title_property = task_title_property
        self.task_status_property = task_status_property
        self.task_assignee_property = task_assignee_property
        self.task_description_property = task_description_property
        self.task_priority_property = task_priority_property
        self.task_due_date_property = task_due_date_property
        self.task_tags_property = task_tags_property
        self.archive_mode = archive_mode

    @property
    def serialize(self):
        return {
            "guild_id": self.guild_id,
            "notion_api_key": self.notion_api_key,
            "notion_db_id": self.notion_db_id,
            "tag": self.tag,
            "prefix": self.prefix,
            "ollama_base_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "task_title_property": self.task_title_property,
            "task_status_property": self.task_status_property,
            "task_assignee_property": self.task_assignee_property,
            "task_description_property": self.task_description_property,
            "task_priority_property": self.task_priority_property,
            "task_due_date_property": self.task_due_date_property,
            "task_tags_property": self.task_tags_property,
            "archive_mode": self.archive_mode,
        }


class AssigneeMapping(Base):
    """Maps a Discord user to a Notion assignee value for a specific guild."""
    __tablename__ = 'assignee_mappings'

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, index=True, nullable=False)
    discord_user_id = Column(String, nullable=False)
    discord_name = Column(String, nullable=True)
    notion_assignee_value = Column(String, nullable=False)

    def __init__(self, guild_id, discord_user_id, notion_assignee_value, discord_name=None):
        self.guild_id = guild_id
        self.discord_user_id = discord_user_id
        self.discord_name = discord_name
        self.notion_assignee_value = notion_assignee_value

    @property
    def serialize(self):
        return {
            "guild_id": self.guild_id,
            "discord_user_id": self.discord_user_id,
            "discord_name": self.discord_name,
            "notion_assignee_value": self.notion_assignee_value,
        }
