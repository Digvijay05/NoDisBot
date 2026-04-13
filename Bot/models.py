import os

from sqlalchemy import Column, Integer, String

try:
    from Bot.database import Base
except ImportError:  # pragma: no cover - script execution fallback
    from database import Base

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
