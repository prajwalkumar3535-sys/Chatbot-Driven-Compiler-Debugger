"""
ollama_client.py - Robust Client for Local Ollama LLMs
Handles token-by-token streaming, intelligent model routing, health checks,
and graceful offline simulations.
"""

import os
import json
import socket
import asyncio
import requests
from typing import AsyncGenerator, Dict, Any, List, Optional

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

def get_installed_model_tags() -> List[str]:
    """Returns simple list of installed model tags (e.g. ['llama3.2:1b', 'qwen2.5-coder:1.5b'])."""
    models = get_ollama_models()
    return [m.get("name") for m in models if m.get("name")]

def resolve_best_model(requested: str, family_hint: Optional[str] = None) -> str:
    """
    Intelligently maps any requested model or family keyword ('qwen', 'phi3', 'llama', etc.)
    to the best matching *installed* local Ollama model.
    """
    if not requested:
        requested = family_hint or "phi3"

    req = requested.lower().strip()
    installed = get_installed_model_tags()

    if not installed:
        return requested

    # 1. Exact match against installed models
    for inst in installed:
        inst_lower = inst.lower()
        if inst_lower == req or inst_lower == f"{req}:latest" or req == f"{inst_lower}:latest":
            return inst

    # 2. Family & capability matching against installed models
    if "qwen" in req or family_hint == "qwen" or "repair" in req:
        # Prioritize installed Qwen Coder models (e.g. qwen2.5-coder:1.5b)
        coders = [m for m in installed if "qwen" in m.lower() and "coder" in m.lower()]
        if coders:
            return coders[0]
        qwens = [m for m in installed if "qwen" in m.lower()]
        if qwens:
            return qwens[0]

    if "phi" in req or family_hint == "phi" or "detective" in req or "tutor" in req:
        minis = [m for m in installed if "phi" in m.lower() and "mini" in m.lower()]
        if minis:
            return minis[0]
        phis = [m for m in installed if "phi" in m.lower()]
        if phis:
            return phis[0]

    if "llama" in req or family_hint == "llama" or "security" in req:
        llama_fast = [m for m in installed if "llama" in m.lower() and ("1b" in m.lower() or "3.2" in m.lower())]
        if llama_fast:
            return llama_fast[0]
        llamas = [m for m in installed if "llama" in m.lower()]
        if llamas:
            return llamas[0]

    # 3. Partial substring matching
    for inst in installed:
        if req in inst.lower() or inst.lower() in req:
            return inst

    # 4. Safe fallback to any installed model
    return installed[0]

async def stream_ollama_response(
    prompt: str,
    model: str,
    temperature: float = 0.2,
    num_predict: int = 500,
    timeout: float = 120.0
) -> AsyncGenerator[str, None]:
    """
    Streams generated tokens from Ollama API using chunked HTTP transfer.
    Automatically resolves model tags to installed local models and handles fallbacks.
    """
    is_online = check_ollama_health()
    if not is_online:
        yield f"⚠️ **Ollama is Offline**\n\nThe AI assistant was unable to reach the local Ollama server at `{OLLAMA_BASE_URL}`.\n\n"
        yield "To enable local inference with full multi-agent streaming:\n"
        yield f"```bash\n# 1. Start the Ollama daemon\nollama serve\n\n# 2. Pull the model\nollama pull {model}\n```\n\n"
        yield "*(Simulated offline mode: verify your Ollama server is started and accessible)*"
        return

    # Automatically resolve model to best installed candidate
    active_model = resolve_best_model(model)

    payload = {
        "model": active_model,
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

    # Handle 404 Model Not Found by falling back to any available model
    if resp.status_code == 404:
        installed = get_installed_model_tags()
        fallback = installed[0] if installed else None
        if fallback and fallback != active_model:
            yield f"*(Note: Model `{active_model}` not found, auto-routed to installed `{fallback}`)*\n\n"
            payload["model"] = fallback
            try:
                resp = requests.post(OLLAMA_GEN_URL, json=payload, stream=True, timeout=(3, timeout), proxies={"http": None, "https": None})
            except Exception as e:
                yield f"⚠️ Inference Fallback Error: {str(e)}"
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
