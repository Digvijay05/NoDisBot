"""
Notion database schema validator.

Fetches database metadata from Notion and checks that the required
task properties exist, using the guild's configured property-name mappings.
"""

import requests

NOTION_API_VERSION = "2022-06-28"
REQUEST_TIMEOUT = 10  # seconds


class SchemaValidationResult:
    """Result of validating a Notion database schema."""

    def __init__(self, valid, missing=None, found=None, warnings=None, resolved_schema=None):
        self.valid = valid
        self.missing = missing or []
        self.found = found or []
        self.warnings = warnings or []
        self.resolved_schema = resolved_schema or {}

    @property
    def summary(self):
        """Human-readable summary for Discord embeds."""
        lines = []
        if self.found:
            lines.append("✅ **Found:** " + ", ".join(self.found))
        if self.missing:
            lines.append("❌ **Missing:** " + ", ".join(self.missing))
        if self.warnings:
            for w in self.warnings:
                lines.append(f"⚠️ {w}")
        return "\n".join(lines) if lines else "No properties checked."


def _get_headers(api_key):
    return {
        "Authorization": api_key,
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def fetch_database_properties(api_key, db_id):
    """Fetch the properties dict from a Notion database.

    Returns (properties_dict, error_string | None).
    """
    url = f"https://api.notion.com/v1/databases/{db_id}"
    try:
        resp = requests.get(url, headers=_get_headers(api_key), timeout=REQUEST_TIMEOUT)
    except requests.Timeout:
        return None, "Notion API request timed out."
    except requests.RequestException as exc:
        return None, f"Notion API request failed: {exc}"

    if resp.status_code != 200:
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        code = body.get("code", "unknown")
        msg = body.get("message", resp.text[:200])
        return None, f"Notion returned {resp.status_code} ({code}): {msg}"

    data = resp.json()
    return data.get("properties", {}), None


def validate_schema(api_key, db_id, property_map=None):
    """Validate a Notion database has the required task properties.

    Args:
        api_key: Notion integration token (decrypted).
        db_id: Notion database ID.
        property_map: dict mapping internal names to Notion property names.
            Defaults to sensible names if not provided.

    Returns:
        SchemaValidationResult
    """
    defaults = {
        "title": "Task",
        "status": "Status",
        "assignee": "Assignee",
        "description": "Description",
        "priority": "Priority",
        "due_date": "Due Date",
        "tags": "Tags",
    }
    mapping = {**defaults, **(property_map or {})}

    properties, error = fetch_database_properties(api_key, db_id)
    if error:
        return SchemaValidationResult(valid=False, warnings=[error])

    prop_names = set(properties.keys())

    found = []
    missing = []
    warnings = []
    resolved_schema = {}

    for internal_name, notion_name in mapping.items():
        if notion_name in properties:
            found.append(notion_name)
            resolved_schema[internal_name] = {
                "name": notion_name,
                "type": properties[notion_name].get("type", "unknown")
            }
        else:
            missing.append(notion_name)

    # Check for optional archive property
    if "Archived" in properties:
        found.append("Archived")
        resolved_schema["archived"] = {
            "name": "Archived",
            "type": properties["Archived"].get("type", "checkbox")
        }
    else:
        warnings.append("No 'Archived' property found — archive will use status-based strategy.")

    valid = len(missing) == 0
    return SchemaValidationResult(valid=valid, missing=missing, found=found, warnings=warnings, resolved_schema=resolved_schema)
