import pytest
from Bot.functionality.notion_tasks import build_notion_properties

def test_build_notion_properties_structures():
    # Setup mock property map definitions 
    # matching the ones provided by notion_schema
    property_map = {
        "title": {"name": "Task Name", "type": "title"},
        "status": {"name": "Status", "type": "select"},
        "priority": {"name": "Priority", "type": "select"},
        "assignee": {"name": "Assigned", "type": "people"},
        "description": {"name": "Details", "type": "rich_text"}
    }
    
    task_data = {
        "title": "Fix bug",
        "status": "In Progress",
        "priority": "High",
        "assignee": "e8c897f2-1f4a-4e4b-8e27-6f882beaf6fa", # Valid UUID mock
        "description": "It breaks on login"
    }
    
    payload = build_notion_properties(task_data, property_map)
    
    assert "Task Name" in payload
    assert payload["Task Name"] == {"title": [{"text": {"content": "Fix bug"}}]}
    
    assert "Status" in payload
    assert payload["Status"] == {"select": {"name": "In Progress"}}
    
    assert "Priority" in payload
    assert payload["Priority"] == {"select": {"name": "High"}}
    
    assert "Assigned" in payload
    assert payload["Assigned"] == {"people": [{"id": "e8c897f2-1f4a-4e4b-8e27-6f882beaf6fa"}]}
    
    assert "Details" in payload
    assert payload["Details"] == {"rich_text": [{"text": {"content": "It breaks on login"}}]}

def test_build_notion_properties_unset_omission():
    property_map = {
        "title": {"name": "Name", "type": "title"},
        "status": {"name": "Status", "type": "select"}
    }
    
    # Status is explicitly None (unset optional field)
    task_data = {
        "title": "Hello",
        "status": None
    }
    
    payload = build_notion_properties(task_data, property_map)
    
    assert "Name" in payload
    assert "Status" not in payload # Should be omitted because it's None

def test_build_notion_properties_rejects_invalid_people_type():
    property_map = {
        "assignee": {"name": "Assigned", "type": "people"}
    }
    
    task_data = {
        "assignee": "Bob" # Not a UUID, should be rejected by internal _is_uuid
    }
    
    payload = build_notion_properties(task_data, property_map)
    
    assert "Assigned" not in payload

def test_build_notion_properties_unmapped_fields_ignored():
    property_map = {
        "title": {"name": "Name", "type": "title"}
    }
    
    task_data = {
        "title": "Hello",
        "fake_field": "Should not appear"
    }
    
    payload = build_notion_properties(task_data, property_map)
    
    assert "Name" in payload
    assert len(payload) == 1
