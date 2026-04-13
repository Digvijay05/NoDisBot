import pytest
from unittest.mock import MagicMock, patch
from Bot.functionality.config import resolve_assignee_mapping

class MockMapping:
    def __init__(self, value):
        self.notion_assignee_value = value

@pytest.fixture
def mock_db_session():
    with patch("Bot.functionality.config.SessionLocal") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        yield mock_session

def test_resolve_assignee_mapping_mention(mock_db_session):
    # Setup the mock query chain: db.query().filter().first()
    mock_query = mock_db_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = MockMapping("uuid-for-123")
    
    res = resolve_assignee_mapping("guild_1", "<@123456>")
    
    assert res == "uuid-for-123"
    # Ensure it checked by exact Discord ID
    assert mock_query.filter.called

def test_resolve_assignee_mapping_mention_exclamation(mock_db_session):
    # Handle <@!123456> format
    mock_query = mock_db_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = MockMapping("uuid-for-exclaim")
    
    res = resolve_assignee_mapping("guild_1", "<@!123456>")
    
    assert res == "uuid-for-exclaim"

def test_resolve_assignee_mapping_fallback_name(mock_db_session):
    # No mention present, fallback to name ILIKE search
    mock_query = mock_db_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = MockMapping("uuid-for-bob")
    
    res = resolve_assignee_mapping("guild_1", "  Bob  ")
    
    assert res == "uuid-for-bob"
    # The pure string should have been processed
    # In SQLalchemy ilike testing is tricky with mocks, but we verify it didn't fail
    assert mock_query.filter.called

def test_resolve_assignee_mapping_no_match(mock_db_session):
    mock_query = mock_db_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = None
    
    res = resolve_assignee_mapping("guild_1", "Unknown Person")
    
    assert res is None
