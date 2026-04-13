import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from aiohttp import ClientError
import asyncio

from Bot.functionality.notion_tasks import (
    create_task, 
    update_task, 
    archive_task, 
    _make_request
)

@pytest.fixture
def mock_prop_map():
    return {
        "title": {"name": "Task Name", "type": "title"},
        "status": {"name": "Status", "type": "select"},
        "archived": {"name": "Archived", "type": "checkbox"}
    }

@pytest.mark.asyncio
@patch("Bot.functionality.notion_tasks.aiohttp.ClientSession.request")
async def test_make_request_success(mock_request):
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"id": "123"}
    
    # Setup async context manager mock
    mock_request.return_value.__aenter__.return_value = mock_resp
    
    res = await _make_request("POST", "fake", "key")
    assert res["ok"] is True
    assert res["data"] == {"id": "123"}

@pytest.mark.asyncio
@patch("Bot.functionality.notion_tasks.aiohttp.ClientSession.request")
async def test_make_request_timeout(mock_request):
    mock_request.side_effect = asyncio.TimeoutError()
    
    res = await _make_request("POST", "fake", "key")
    assert res["ok"] is False
    assert res["error_type"] == "timeout"

@pytest.mark.asyncio
@patch("Bot.functionality.notion_tasks.aiohttp.ClientSession.request")
async def test_make_request_network_failed(mock_request):
    mock_request.side_effect = ClientError("Connection reset")
    
    res = await _make_request("POST", "fake", "key")
    assert res["ok"] is False
    assert res["error_type"] == "network_error"

@pytest.mark.asyncio
@patch("Bot.functionality.notion_tasks.aiohttp.ClientSession.request")
async def test_make_request_api_error_normalization(mock_request):
    mock_resp = AsyncMock()
    mock_resp.status = 400
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json.return_value = {"message": "Invalid request"}
    
    mock_request.return_value.__aenter__.return_value = mock_resp
    
    res = await _make_request("POST", "fake", "key")
    assert res["ok"] is False
    assert res["error_type"] == "api_error"
    assert "Invalid request" in res["message"]

@pytest.mark.asyncio
@patch("Bot.functionality.notion_tasks._make_request")
async def test_archive_strategy_notion_archive(mock_make, mock_prop_map):
    # Tests the standard "notion_archive" mode which sends {"archived": True}
    mock_make.return_value = {"ok": True, "data": {}}
    
    res = await archive_task("key", "page_1", mock_prop_map, archive_mode="notion_archive")
    
    assert res["ok"] is True
    mock_make.assert_called_once()
    called_json = mock_make.call_args[1]["json_data"]
    assert called_json == {"archived": True}

@pytest.mark.asyncio
@patch("Bot.functionality.notion_tasks._make_request")
async def test_archive_strategy_checkbox(mock_make, mock_prop_map):
    mock_make.return_value = {"ok": True, "data": {}}
    
    res = await archive_task("key", "page_1", mock_prop_map, archive_mode="checkbox")
    
    assert res["ok"] is True
    called_json = mock_make.call_args[1]["json_data"]
    assert called_json == {"properties": {"Archived": {"checkbox": True}}}

@pytest.mark.asyncio
@patch("Bot.functionality.notion_tasks._make_request")
async def test_archive_strategy_status(mock_make, mock_prop_map):
    mock_make.return_value = {"ok": True, "data": {}}
    
    res = await archive_task("key", "page_1", mock_prop_map, archive_mode="status", archive_value="Done")
    
    assert res["ok"] is True
    called_json = mock_make.call_args[1]["json_data"]
    assert called_json == {"properties": {"Status": {"select": {"name": "Done"}}}}

@pytest.mark.asyncio
async def test_archive_strategy_invalid(mock_prop_map):
    # Test setting checkbox mode without a valid property configured
    bad_map = {"title": {"name": "Task Name", "type": "title"}} # Missing archived prop
    
    res = await archive_task("key", "page_1", bad_map, archive_mode="checkbox")
    assert res["ok"] is False
    assert res["error_type"] == "configuration_error"
    
    res2 = await archive_task("key", "page_1", bad_map, archive_mode="unknown_mode")
    assert res2["ok"] is False
    assert res2["error_type"] == "configuration_error"
