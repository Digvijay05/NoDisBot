"""
Notion Tasks Service.

Handles async creation, updating, hunting, and archiving of tasks
in Notion via strict schema validation.
"""

import aiohttp
import asyncio

NOTION_API_VERSION = "2022-06-28"
REQUEST_TIMEOUT = 10  # seconds


def _get_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}" if not api_key.startswith("Bearer ") else api_key,
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }


def _build_property_payload(prop_config: dict, value) -> dict:
    """Builds a Notion property payload based on its strict type definition."""
    ptype = prop_config.get("type")
    
    if ptype == "title":
        return {"title": [{"text": {"content": str(value)}}]}
        
    elif ptype == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}]}
        
    elif ptype == "status":
        return {"status": {"name": str(value)}}
        
    elif ptype == "select":
        return {"select": {"name": str(value)}}
        
    elif ptype == "multi_select":
        # Expecting an array of strings
        if isinstance(value, list):
            return {"multi_select": [{"name": str(v)} for v in value]}
        return {"multi_select": [{"name": str(value)}]}
        
    elif ptype == "date":
        return {"date": {"start": str(value)}}
        
    elif ptype == "people":
        # Requires a valid Notion UUID
        return {"people": [{"id": str(value)}]}
        
    elif ptype == "checkbox":
        # Requires boolean
        return {"checkbox": bool(value)}
        
    return {}


def build_notion_properties(task_data: dict, property_map: dict) -> dict:
    """
    Generates a full properties payload given the normalized task data
    and the strict property_map output by notion_schema.
    """
    properties = {}
    
    for key, value in task_data.items():
        if value is None:
            continue
            
        if key in property_map:
            prop_config = property_map[key]
            prop_name = prop_config["name"]
            prop_type = prop_config["type"]
            
            # Special check for "people" assignee without exact ID map validation
            if key == "assignee" and prop_type == "people" and not _is_uuid(value):
                # The caller should have warned or rejected this earlier, but we catch it just in case
                continue
                
            payload = _build_property_payload(prop_config, value)
            if payload:
                properties[prop_name] = payload
                
    return properties


def _is_uuid(val: str) -> bool:
    """Naive UUID check to ensure we don't send Discord names to Notion people fields."""
    return isinstance(val, str) and len(val) >= 32 and "-" in val


async def _make_request(method: str, url: str, api_key: str, json_data: dict = None) -> dict:
    """Internal helper to dispatch aiohttp requests."""
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, url, headers=_get_headers(api_key), json=json_data) as response:
                body = await response.json() if "application/json" in response.headers.get("content-type", "") else {}
                
                if response.status != 200:
                    return {
                        "ok": False,
                        "error_type": "api_error",
                        "status": response.status,
                        "message": body.get("message", f"Notion API error: {response.status}")
                    }
                    
                return {
                    "ok": True,
                    "data": body
                }
    except asyncio.TimeoutError:
        return {"ok": False, "error_type": "timeout", "message": "Notion API request timed out."}
    except aiohttp.ClientError as e:
        return {"ok": False, "error_type": "network_error", "message": f"Network error during Notion call: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error_type": "unknown", "message": f"Unexpected error: {str(e)}"}


async def create_task(api_key: str, db_id: str, task_data: dict, property_map: dict) -> dict:
    """Create a new task in the specified Notion DB."""
    
    # Pre-flight assignee validation requirement for MVP
    if "assignee" in task_data and task_data["assignee"]:
        assignee_config = property_map.get("assignee", {})
        if assignee_config.get("type") == "people" and not _is_uuid(task_data["assignee"]):
            return {
                "ok": False,
                "error_type": "validation_error",
                "message": "Assignee property is configured as Notion People, but no valid Notion user mapping was found for this Discord user."
            }

    properties_payload = build_notion_properties(task_data, property_map)
    if not properties_payload:
        return {"ok": False, "error_type": "validation_error", "message": "No valid properties generated for task payload."}
        
    payload = {
        "parent": {"database_id": db_id},
        "properties": properties_payload
    }
    
    url = "https://api.notion.com/v1/pages"
    return await _make_request("POST", url, api_key, json_data=payload)


async def update_task(api_key: str, page_id: str, task_data: dict, property_map: dict) -> dict:
    """Update an existing task."""
    
    if "assignee" in task_data and task_data["assignee"]:
        assignee_config = property_map.get("assignee", {})
        if assignee_config.get("type") == "people" and not _is_uuid(task_data["assignee"]):
            return {
                "ok": False,
                "error_type": "validation_error",
                "message": "Assignee property is configured as Notion People, but no valid Notion user mapping was found for this Discord user."
            }

    properties_payload = build_notion_properties(task_data, property_map)
    if not properties_payload:
        return {"ok": False, "error_type": "validation_error", "message": "No valid properties generated for task update."}

    payload = {"properties": properties_payload}
    url = f"https://api.notion.com/v1/pages/{page_id}"
    return await _make_request("PATCH", url, api_key, json_data=payload)


async def archive_task(api_key: str, page_id: str, property_map: dict, archive_mode: str, archive_value: str = None) -> dict:
    """
    Archive a task deterministically based on configuration strategy.
    
    Supported archive_modes:
    1. "notion_archive": Sets the page to {archived: true}
    2. "checkbox": Sets a dedicated archive checkbox to true
    3. "status": Sets the status property to a specified archive_value
    """
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    
    if archive_mode == "notion_archive":
        return await _make_request("PATCH", url, api_key, json_data={"archived": True})
        
    elif archive_mode == "checkbox":
        archived_config = property_map.get("archived")
        if not archived_config or archived_config.get("type") != "checkbox":
             return {
                 "ok": False, 
                 "error_type": "configuration_error", 
                 "message": "Archive mode set to 'checkbox' but no valid Checkbox property 'Archived' mapped."
             }
        
        payload = {"properties": {archived_config["name"]: {"checkbox": True}}}
        return await _make_request("PATCH", url, api_key, json_data=payload)

    elif archive_mode == "status":
        if not archive_value:
            return {
                 "ok": False, 
                 "error_type": "configuration_error", 
                 "message": "Archive mode set to 'status' but no archive status value provided."
             }
        status_config = property_map.get("status")
        if not status_config:
             return {
                 "ok": False, 
                 "error_type": "configuration_error", 
                 "message": "Archive mode set to 'status' but no status property is mapped."
             }
        
        # Determine if the mapped status column is type "status" or "select"
        stype = status_config.get("type")
        if stype not in ["status", "select"]:
             return {
                 "ok": False, 
                 "error_type": "configuration_error", 
                 "message": f"Mapped status property must be 'status' or 'select', got '{stype}'."
             }
        
        # Build the proper nested payload
        payload = {"properties": {status_config["name"]: {stype: {"name": archive_value}}}}
        return await _make_request("PATCH", url, api_key, json_data=payload)
        
    else:
        return {
             "ok": False, 
             "error_type": "configuration_error", 
             "message": f"Unknown archive mode: '{archive_mode}'."
         }


async def search_tasks(api_key: str, db_id: str, query_filters: dict, property_map: dict) -> dict:
    """
    Search tasks. For MVP, we build a simple generic query or title filter.
    Returns the standard wrapped response.
    """
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    
    payload = {}
    
    filters = []
    
    if query_filters.get("title") and "title" in property_map:
        filters.append({
            "property": property_map["title"]["name"],
            "title": {"contains": query_filters["title"]}
        })
        
    if query_filters.get("status") and "status" in property_map:
        stype = property_map["status"]["type"]
        filters.append({
            "property": property_map["status"]["name"],
            stype: {"equals": query_filters["status"]}
        })

    # You could add other attributes here later like priority or tags
    if query_filters.get("priority") and "priority" in property_map:
        ptype = property_map["priority"]["type"]
        filters.append({
            "property": property_map["priority"]["name"],
            ptype: {"equals": query_filters["priority"]}
        })

    if len(filters) == 1:
        payload["filter"] = filters[0]
    elif len(filters) > 1:
        payload["filter"] = {"and": filters}
        
    # Default sorting for freshest first if no explicit sorting
    if "sorts" not in payload:
        payload["sorts"] = [{"timestamp": "last_edited_time", "direction": "descending"}]
        
    result = await _make_request("POST", url, api_key, json_data=payload)
    if result["ok"]:
        # Unwrap data structure down to list of items to make it easier for callers,
        # but maintaining the same return schema format.
        result["results"] = result["data"].get("results", [])
    return result
