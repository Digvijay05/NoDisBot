import pytest
from Bot.functionality.task_resolution import resolve_task_candidates

def create_mock_task(task_id: str, title: str):
    return {
        "id": task_id,
        "properties": {
            "Task Title": {
                "type": "title",
                "title": [{"text": {"content": title}}]
            }
        }
    }

def test_resolve_no_match():
    results = []
    status, result = resolve_task_candidates(results, "Fix bug")
    assert status == "no_match"
    assert result is None

def test_resolve_exact_match_beats_fuzzy():
    results = [
        create_mock_task("1", "Fix bug in login"),
        create_mock_task("2", "Fix bug"), # Exact match
        create_mock_task("3", "Fix bug on mobile")
    ]
    status, result = resolve_task_candidates(results, "Fix bug")
    assert status == "resolved"
    assert result["id"] == "2"

def test_resolve_ambiguous_match():
    results = [
        create_mock_task("1", "Fix bug in login"),
        create_mock_task("3", "Fix bug on mobile")
    ]
    status, result = resolve_task_candidates(results, "Fix bug")
    assert status == "ambiguous"
    assert len(result) == 2 # Candidate list
    assert result[0]["id"] == "1"

def test_resolve_single_fuzzy_match():
    # Only one fuzzy match returned from Notion
    results = [
        create_mock_task("1", "Fix bug in login")
    ]
    status, result = resolve_task_candidates(results, "Fix bug")
    assert status == "resolved"
    assert result["id"] == "1"

def test_resolve_exact_case_insensitivity():
    results = [
        create_mock_task("1", "FIX BUG")
    ]
    status, result = resolve_task_candidates(results, "fix bug")
    assert status == "resolved"
    assert result["id"] == "1"
