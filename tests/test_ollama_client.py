import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from aiohttp import ClientConnectorError

from Bot.functionality.ollama_client import generate_chat_completion

@pytest.mark.asyncio
@patch("Bot.functionality.ollama_client.aiohttp.ClientSession.post")
async def test_generate_chat_completion_success(mock_post):
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {
        "message": {"content": '{"action": "create"}'}
    }
    
    mock_post.return_value.__aenter__.return_value = mock_resp
    
    content, error = await generate_chat_completion(
        "http://localhost:11434", 
        "llama3", 
        "sys", 
        "user"
    )
    
    assert error is None
    assert content == '{"action": "create"}'
    
    # Verify the payload structure
    called_url = mock_post.call_args[0][0]
    called_json = mock_post.call_args[1]["json"]
    assert called_url == "http://localhost:11434/api/chat"
    assert called_json["format"] == "json"
    assert len(called_json["messages"]) == 2

@pytest.mark.asyncio
@patch("Bot.functionality.ollama_client.aiohttp.ClientSession.post")
async def test_generate_chat_completion_non_200(mock_post):
    mock_resp = AsyncMock()
    mock_resp.status = 500
    mock_resp.text.return_value = "Internal Server Error"
    
    mock_post.return_value.__aenter__.return_value = mock_resp
    
    content, error = await generate_chat_completion("url", "model", "sys", "user")
    
    assert content is None
    assert "HTTP 500" in error
    assert "Internal Server Error" in error

@pytest.mark.asyncio
@patch("Bot.functionality.ollama_client.aiohttp.ClientSession.post")
async def test_generate_chat_completion_empty_response(mock_post):
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json.return_value = {"message": {"content": ""}}
    
    mock_post.return_value.__aenter__.return_value = mock_resp
    
    content, error = await generate_chat_completion("url", "model", "sys", "user")
    
    assert content is None
    assert "empty response" in error

@pytest.mark.asyncio
@patch("Bot.functionality.ollama_client.aiohttp.ClientSession.post")
async def test_generate_chat_completion_timeout(mock_post):
    mock_post.side_effect = asyncio.TimeoutError()
    
    content, error = await generate_chat_completion("url", "model", "sys", "user")
    
    assert content is None
    assert "timed out" in error

@pytest.mark.asyncio
@patch("Bot.functionality.ollama_client.aiohttp.ClientSession.post")
async def test_generate_chat_completion_connection_error(mock_post):
    # aiohttp requires connection key or similar, mock it roughly
    err = ClientConnectorError(connection_key=None, os_error=OSError("Refused"))
    mock_post.side_effect = err
    
    content, error = await generate_chat_completion("url", "model", "sys", "user")
    
    assert content is None
    assert "Could not connect" in error
