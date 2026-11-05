"""
ollama_client.py - Client for Local Ollama LLMs
Handles token-by-token streaming, health checks, model discovery, and offline simulations.
"""

import os
import json
import socket
import asyncio
import requests
from typing import AsyncGenerator, Dict, Any, List

OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_GEN_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

def _sync_check_health(timeout: float = 0.3) -> bool:
    try:
        s = socket.create_connection(('127.0.0.1', 11434), timeout=timeout)
        s.close()
        r = requests.get(OLLAMA_TAGS_URL, timeout=timeout, proxies={"http": None, "https": None})
        return r.status_code == 200
    except Exception:
        return False

def check_ollama_health(timeout: float = 0.3) -> bool:
    """Fast check if Ollama daemon is reachable."""
    return _sync_check_health(timeout)

def _sync_get_models() -> List[Dict[str, Any]]:
    if not _sync_check_health(0.2):
        return []
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=1.0, proxies={"http": None, "https": None})
        if r.status_code == 200:
            return r.json().get("models", [])
    except Exception:
        pass
    return []

def get_ollama_models() -> List[Dict[str, Any]]:
    """Fetches list of available models installed in local Ollama."""
    return _sync_get_models()

async def stream_ollama_response(
    prompt: str,
    model: str,
    temperature: float = 0.2,
    num_predict: int = 500,
    timeout: float = 120.0
) -> AsyncGenerator[str, None]:
    """
    Streams generated tokens from Ollama API using chunked HTTP transfer.
    Falls back to a structured simulation if Ollama server is offline.
    """
    is_online = check_ollama_health()
    if not is_online:
        yield f"⚠️ **Ollama is Offline**\n\nThe AI assistant was unable to reach the local Ollama server at `{OLLAMA_BASE_URL}`.\n\n"
        yield "To enable local inference with full multi-agent streaming:\n"
        yield f"```bash\n# 1. Start the Ollama daemon\nollama serve\n\n# 2. Pull the model\nollama pull {model}\n```\n\n"
        yield "*(Simulated offline mode: verify your Ollama server is started and accessible)*"
        return

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict
        }
    }

    try:
        resp = requests.post(OLLAMA_GEN_URL, json=payload, stream=True, timeout=(3, timeout), proxies={"http": None, "https": None})
    except Exception as e:
        yield f"⚠️ Inference Connection Error: {str(e)}"
        return

    if resp.status_code != 200:
        yield f"⚠️ Ollama error (HTTP {resp.status_code}): {resp.text}"
        return

    for line in resp.iter_lines():
        if line:
            try:
                chunk = json.loads(line)
                token = chunk.get("response", "")
                if token:
                    yield token
                if chunk.get("done", False):
                    break
            except Exception:
                continue
        await asyncio.sleep(0.005)
