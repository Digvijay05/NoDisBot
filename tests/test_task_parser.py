import pytest
from unittest.mock import patch, AsyncMock
import json

from Bot.functionality.task_parser import (
    normalize_status,
    normalize_priority,
    clean_json_response,
    parse_task_request
)

def test_status_normalization():
    assert normalize_status("done") == "Done"
    assert normalize_status("completed") == "Done"
    assert normalize_status("wip") == "In Progress"
    assert normalize_status("doing") == "In Progress"
    assert normalize_status("later") == "Backlog"
    assert normalize_status("idea") == "Backlog"
    assert normalize_status("random_unmatched") == "To Do"
    assert normalize_status("") is None
    assert normalize_status(None) is None

def test_priority_normalization():
    assert normalize_priority("p0") == "High"
    assert normalize_priority("urgent") == "High"
    assert normalize_priority("p4") == "Low"
    assert normalize_priority("trivial") == "Low"
    assert normalize_priority("normal") == "Medium"
    assert normalize_priority("") is None
    assert normalize_priority(None) is None

def test_clean_json_response_handles_fences():
    # Exact fencing
    assert clean_json_response('```json\n{"key": "value"}\n```') == '{"key": "value"}'
    
    # Generic fencing
    assert clean_json_response('```\n{"key": "value"}```') == '{"key": "value"}'
    
    # No fencing
    assert clean_json_response('{"key": "value"}') == '{"key": "value"}'

@pytest.mark.asyncio
@patch("Bot.functionality.task_parser.generate_chat_completion")
async def test_parse_task_request_success(mock_generate):
    # Setup mock to return a perfect JSON string
    mock_generate.return_value = (
        '{"action": "create", "task": {"title": "Test Task", "status": "wip", "priority": "urgent"}}',
        None
    )
    
    parsed, err = await parse_task_request("Do a test task", "http://fake", "fake-model")
    
    assert err is None
    assert parsed["action"] == "create"
    # Verify normalization was applied
    assert parsed["task"]["status"] == "In Progress"
    assert parsed["task"]["priority"] == "High"

@pytest.mark.asyncio
@patch("Bot.functionality.task_parser.generate_chat_completion")
async def test_parse_task_request_missing_required_fields(mock_generate):
    # Setup mock to return JSON missing 'action' or 'task'
    mock_generate.return_value = ('{"task": {"title": "No action given"}}', None)
    
    parsed, err = await parse_task_request("No action task", "http://fake", "fake-model")
    
    # parse_task_request relies purely on the dict structure. 
    # If action is missing, the parsed object just won't have it.
    # Current implementation doesn't strictly block missing fields, it just passes the dict.
    assert err is None
    assert "action" not in parsed
    assert parsed["task"]["title"] == "No action given"

@pytest.mark.asyncio
@patch("Bot.functionality.task_parser.generate_chat_completion")
async def test_parse_task_request_malformed_json(mock_generate):
    # Setup mock to return completely broken JSON
    mock_generate.return_value = ('This is just extra text { not json', None)
    
    parsed, err = await parse_task_request("Break this", "http://fake", "fake-model")
    
    assert parsed is None
    assert "Failed to parse LLM response into JSON" in err

@pytest.mark.asyncio
@patch("Bot.functionality.task_parser.generate_chat_completion")
async def test_parse_task_request_llm_error(mock_generate):
    # Setup mock to simulate network/LLM error from the client layer
    mock_generate.return_value = (None, "Ollama connection timeout")
    
    parsed, err = await parse_task_request("Time me out", "http://fake", "fake-model")
    
    assert parsed is None
    assert err == "Ollama connection timeout"
