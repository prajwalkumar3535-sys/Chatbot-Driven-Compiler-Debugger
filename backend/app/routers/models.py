"""
routers/models.py - Model, Language, Agent Metadata & System Health Endpoints
"""

import sys
import os
from fastapi import APIRouter
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from language_config import LANGUAGE_CONFIG, ALLOWED_LANGUAGES, get_language_config
from multiagent_platform import (
    MODEL_REGISTRY,
    DEFAULT_FAMILY_MODELS,
    DiagnosticAgent,
    RepairAgent,
    SecurityAuditorAgent,
    TutorAgent
)
from language_executor import is_docker_engine_ready
from app.ollama_client import check_ollama_health, get_ollama_models

router = APIRouter(prefix="/api", tags=["metadata"])

@router.get("/health")
def get_health():
    """Returns real-time health for Ollama server and Docker sandbox daemon."""
    ollama_ok = check_ollama_health()
    docker_ok = is_docker_engine_ready()

    sandboxes = {
        lang: LANGUAGE_CONFIG[lang]["docker_image"]
        for lang in ALLOWED_LANGUAGES
    }

    return {
        "status": "online",
        "ollama_online": ollama_ok,
        "docker_online": docker_ok,
        "sandboxes": sandboxes
    }

@router.get("/languages")
def get_languages():
    """Returns supported languages, starter templates, and compilation specifications."""
    languages = []
    for lang_key in ALLOWED_LANGUAGES:
        cfg = LANGUAGE_CONFIG[lang_key]
        languages.append({
            "id": lang_key,
            "name": cfg["display_name"],
            "extension": cfg["extension"],
            "filename": cfg["source_filename"],
            "needs_compile": cfg["needs_compile"],
            "docker_image": cfg["docker_image"],
            "memory_limit": cfg["memory_limit"],
            "template": cfg["default_code"]
        })
    return languages

@router.get("/models")
def get_models():
    """Returns registered LLMs (Llama 3, Phi-3, Qwen 2.5) merged with local Ollama tags."""
    installed_models = get_ollama_models()
    installed_names = [m.get("name") for m in installed_models if m.get("name")]

    result = []
    for tag, info in MODEL_REGISTRY.items():
        is_installed = any(tag in inst or inst in tag for inst in installed_names)
        result.append({
            "id": tag,
            "name": info["name"],
            "family": info["family"],
            "description": info["description"],
            "role_affinity": info["role_affinity"],
            "pull_cmd": info["pull_cmd"],
            "is_installed": is_installed
        })

    return {
        "models": result,
        "installed_tags": installed_names,
        "default_family_models": DEFAULT_FAMILY_MODELS
    }

@router.get("/agents")
def get_agents():
    """Returns the 4 specialized agents, their default models, icons, and system prompts."""
    diag = DiagnosticAgent()
    rep = RepairAgent()
    sec = SecurityAuditorAgent()
    tut = TutorAgent()

    agents = [
        {
            "id": "tutor",
            "name": "Tutor Mentor",
            "icon": "GraduationCap",
            "role": tut.role,
            "accent_color": "#10b981", # Emerald
            "default_model": tut.default_model,
            "description": "Pedagogical guide explaining error mechanics, concepts, and time/space complexity.",
            "prompt_template": "Explains why the compiler rejected the code and teaches the core invariants to remember."
        },
        {
            "id": "detective",
            "name": "Detective Agent",
            "icon": "Search",
            "role": diag.role,
            "accent_color": "#3b82f6", # Blue
            "default_model": diag.default_model,
            "description": "Fault localization specialist pinpointing line numbers and root compiler syntax errors.",
            "prompt_template": "Isolates the exact line and syntax/runtime trigger with strict technical precision."
        },
        {
            "id": "repair",
            "name": "Repair Agent",
            "icon": "Wrench",
            "role": rep.role,
            "accent_color": "#8b5cf6", # Purple
            "default_model": rep.default_model,
            "description": "Code architect synthesizing minimal, idiomatic, and bug-free code patches.",
            "prompt_template": "Synthesizes complete, valid replacement code in markdown fences preserving existing logic."
        },
        {
            "id": "security",
            "name": "Security Sentinel",
            "icon": "ShieldAlert",
            "role": sec.role,
            "accent_color": "#ef4444", # Red
            "default_model": sec.default_model,
            "description": "Enforces 13-layer defense checking memory vulnerabilities, buffer overflows, and dangerous APIs.",
            "prompt_template": "Audits proposed fixes against OWASP/CWE standards with automated feedback loops."
        }
    ]

    return agents
