"""
Async HTTP client for interacting with a configured Ollama instance.
"""

import aiohttp
import asyncio
import json

DEFAULT_TIMEOUT = 30  # seconds


async def generate_chat_completion(base_url: str, model: str, system_prompt: str, user_prompt: str):
    """
    Call Ollama's /api/chat endpoint to generate a response.
    
    Requests JSON format implicitly via the prompt setup, and forces
    json format on the Ollama endpoint if supported (Ollama > 0.1.30 supports this).
    """
    
    # Ensure URL doesn't have trailing slash
    base_url = base_url.rstrip("/")
    endpoint = f"{base_url}/api/chat"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json",  # Force Ollama to output valid JSON
        "stream": False
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    return None, f"Ollama HTTP {response.status}: {text}"
                
                data = await response.json()
                message_content = data.get("message", {}).get("content", "")
                
                if not message_content:
                    return None, "Ollama returned an empty response."
                
                return message_content, None
                
    except asyncio.TimeoutError:
        return None, f"Ollama request timed out after {DEFAULT_TIMEOUT} seconds."
    except aiohttp.ClientConnectorError:
        return None, f"Could not connect to Ollama at {base_url}. Is it running?"
    except Exception as e:
        return None, f"Unexpected error calling Ollama: {str(e)}"
