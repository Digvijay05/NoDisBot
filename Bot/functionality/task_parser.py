import json
import re
from datetime import datetime
from .ollama_client import generate_chat_completion

SYSTEM_PROMPT = """You are a natural language task parsing engine. 
Your ONLY job is to take a user's raw message and extract the intended task details.
You MUST output ONLY valid JSON matching the exact schema below. Do not output any conversational text or markdown code blocks.

Schema:
{
  "action": "string", // Must be one of: "create", "update", "move", "assign", "archive", "search"
  "task": {
    "title": "string or null", // The core task to be done.
    "description": "string or null", // Any additional details or requirements.
    "status": "string or null", // Typically: "Backlog", "To Do", "In Progress", "Done".
    "assignee": "string or null", // Look for mentions like @user or a name context.
    "due_date": "string or null", // ISO format YYYY-MM-DD. ONLY provide if the user explicitly says a date or relative time (e.g. "tomorrow"). DO NOT guess.
    "priority": "string or null", // Must be: "High", "Medium", "Low".
    "tags": ["array of strings"]
  }
}

Rules:
1. If the user does not specify a field, set its value to null.
2. If the user mentions "today" or "tomorrow", calculate the date based on the user's input context (assume relative to the provided current date).
3. If it looks like a task addition, `action` should be "create", unless they explicitly ask to update or assign something existing.
4. Keep the title concise and actionable.
5. If you cannot determine the action or title, default to "create" and dump the whole message into the title.
"""

def normalize_status(status: str) -> str:
    """Normalize common status variations to predefined Notion board columns."""
    if not status:
        return None
        
    s = status.lower().strip()
    if s in ["done", "completed", "finished", "resolved", "closed"]:
        return "Done"
    elif s in ["in progress", "wip", "doing", "working on it", "active"]:
        return "In Progress"
    elif s in ["backlog", "idea", "someday", "later"]:
        return "Backlog"
    else:
        # Default or fallback
        return "To Do"

def normalize_priority(priority: str) -> str:
    """Normalize common priority variations."""
    if not priority:
        return None
        
    p = priority.lower().strip()
    if p in ["high", "urgent", "critical", "p0", "p1"]:
        return "High"
    elif p in ["low", "minor", "trivial", "p3", "p4"]:
        return "Low"
    else:
        return "Medium"

def clean_json_response(raw_text: str) -> str:
    """Attempt to strip markdown formatting if the LLM ignores the system prompt."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
        
    if text.endswith("```"):
        text = text[:-3]
        
    return text.strip()

async def parse_task_request(user_input: str, base_url: str, model: str, api_key: str = None) -> tuple:
    """
    Sends natural language input to Ollama and attempts to parse the returned JSON.
    Returns (dict, error_string). If successful, error_string is None.
    """
    # Provide the LLM with the current date to allow relative date math like "tomorrow".
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    context_prefix = f"System Date context: {current_date}\n\nUser Input:\n"
    user_prompt = f"{context_prefix}{user_input}"
    
    raw_content, err = await generate_chat_completion(
        base_url=base_url,
        model=model,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        api_key=api_key,
    )
    
    if err:
        return None, err
        
    cleaned_content = clean_json_response(raw_content)
    
    try:
        parsed_data = json.loads(cleaned_content)
        
        # Apply strict normalization
        if "task" in parsed_data:
            t = parsed_data["task"]
            if t.get("status"):
                t["status"] = normalize_status(t["status"])
            if t.get("priority"):
                t["priority"] = normalize_priority(t["priority"])
                
        return parsed_data, None
        
    except json.JSONDecodeError:
        return None, f"Failed to parse LLM response into JSON. Raw output: {cleaned_content}"
    except Exception as e:
        return None, f"Unexpected error during parsing validation: {str(e)}"
