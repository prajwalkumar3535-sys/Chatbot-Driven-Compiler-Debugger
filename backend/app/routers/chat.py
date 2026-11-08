"""
routers/chat.py - Real-Time Streaming Multi-Agent & Multi-Model Council SSE Endpoint
Enhanced with AST Generator for instant structural context & syntax tree injection,
and dynamic model resolution to prevent 404 errors across local Ollama LLMs.
"""

import sys
import os
import json
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sse_starlette.sse import EventSourceResponse

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.ollama_client import stream_ollama_response, check_ollama_health, resolve_best_model
from app.ast_generator import generate_ast_analysis
from multiagent_platform import (
    MODEL_REGISTRY,
    DEFAULT_FAMILY_MODELS,
    DiagnosticAgent,
    RepairAgent,
    SecurityAuditorAgent,
    TutorAgent,
    resolve_model_alias
)
from error_classifier import classify_error
from fix_engine import validate_ai_fix
from audit_logger import log_interaction

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatStreamRequest(BaseModel):
    agent: Optional[str] = Field(default="tutor", description="tutor | detective | repair | security")
    mode: Optional[str] = Field(default="single", description="single | council | swarm")
    model: Optional[str] = Field(default=None, description="Model tag override")
    language: Optional[str] = Field(default="cpp")
    code: Optional[str] = Field(default="")
    last_run_output: Optional[str] = Field(default="")
    messages: List[ChatMessage] = Field(default_factory=list)

@router.post("/stream")
async def stream_chat(req: ChatStreamRequest):
    """
    Streams multi-agent tokens via Server-Sent Events (SSE).
    Injects AST syntax tree into agent prompts for high-speed fault localization.
    Automatically resolves local Ollama models to prevent 404 errors.
    """
    lang = (req.language or "cpp").lower()
    code = req.code or ""
    error = req.last_run_output or ""
    user_query = req.messages[-1].content if req.messages else "Please review this code."

    # Generate AST Analysis for LLM structural grounding
    ast_data = generate_ast_analysis(code, language=lang)
    ast_block = ast_data.get("ast_prompt_block", "")

    async def event_generator():
        # First event: Emit parsed AST summary
        yield {
            "event": "ast_ready",
            "data": json.dumps({
                "syntax_valid": ast_data.get("syntax_valid", True),
                "summary": ast_data.get("summary", ""),
                "node_count": ast_data.get("node_count", 0),
                "control_flow": ast_data.get("control_flow", {})
            })
        }

        # === MODE 1: MULTI-MODEL COUNCIL MODE ===
        if req.mode == "council":
            yield {
                "event": "council_start",
                "data": json.dumps({"status": "starting", "message": "Convening Multi-Model Council with AST Context..."})
            }

            # Dynamically resolve models to local installed candidates
            council_targets = [
                ("Meta Llama", resolve_best_model("llama")),
                ("Microsoft Phi-3", resolve_best_model("phi")),
                ("Alibaba Qwen", resolve_best_model("qwen"))
            ]

            collected_proposals = {}

            for name, mod in council_targets:
                yield {
                    "event": "model_header",
                    "data": json.dumps({"model_name": name, "model_tag": mod})
                }

                lang_tag = "python" if lang in ("python", "py") else ("java" if lang == "java" else "cpp")
                council_prompt = f"""You are participating in the Multi-Model Program Repair Council.
Language: {lang.upper()}

Original Source Code:
```{lang}
{code}
```

Compiler / Runtime Output:
{error}

{ast_block}

User Query: {user_query}

TASK:
1. Use the provided Abstract Syntax Tree (AST) to pinpoint the exact failure point.
2. Provide your concise diagnosis and suggested fix.
3. Enclose complete, working, compile-ready code in ```{lang_tag} ... ``` code block."""

                model_text = []
                async for token in stream_ollama_response(council_prompt, model=mod, temperature=0.2):
                    model_text.append(token)
                    yield {
                        "event": "token",
                        "data": json.dumps({"model": name, "token": token})
                    }

                full_text = "".join(model_text)
                is_safe, extracted, sec_note = validate_ai_fix(full_text, language=lang)
                collected_proposals[name] = {
                    "text": full_text,
                    "code": extracted,
                    "is_safe": is_safe,
                    "sec_note": sec_note
                }

                yield {
                    "event": "model_audit",
                    "data": json.dumps({
                        "model": name,
                        "is_safe": is_safe,
                        "note": sec_note,
                        "has_code": bool(extracted)
                    })
                }
                await asyncio.sleep(0.05)

            # Final Council Consensus Synthesis
            yield {
                "event": "consensus_start",
                "data": json.dumps({"message": "Synthesizing Council Consensus with AST Guidance..."})
            }

            consensus_prompt = f"""You are the Multi-Model Council Moderator.
Language: {lang.upper()}

Buggy Code:
```{lang}
{code}
```

{ast_block}

Proposals received from Meta Llama, Microsoft Phi-3, and Alibaba Qwen.
Summarize the consensus root cause based on the AST, select the safest fix, and give the student a concise actionable takeaway."""

            moderator_mod = resolve_best_model("phi")
            async for token in stream_ollama_response(consensus_prompt, model=moderator_mod, temperature=0.2):
                yield {
                    "event": "consensus_token",
                    "data": json.dumps({"token": token})
                }

            yield {"event": "done", "data": json.dumps({"is_done": True})}
            return

        # === MODE 2: SINGLE AGENT STREAMING ===
        agent_id = (req.agent or "tutor").lower()
        selected_model = req.model

        if agent_id == "detective":
            prompt = _build_detective_prompt(lang, code, error, user_query, ast_block)
            default_mod = resolve_best_model("phi")
        elif agent_id == "repair":
            prompt = _build_repair_prompt(lang, code, error, user_query, ast_block)
            default_mod = resolve_best_model("qwen")
        elif agent_id == "security":
            prompt = _build_security_prompt(lang, code, error, user_query, ast_block)
            default_mod = resolve_best_model("llama")
        else:
            prompt = _build_tutor_prompt(lang, code, error, user_query, req.messages, ast_block)
            default_mod = resolve_best_model("phi")

        active_model = resolve_best_model(selected_model) if selected_model else default_mod

        yield {
            "event": "agent_start",
            "data": json.dumps({"agent": agent_id, "model": active_model})
        }

        full_response = []
        async for token in stream_ollama_response(prompt, model=active_model, temperature=0.2):
            full_response.append(token)
            yield {
                "event": "token",
                "data": json.dumps({"token": token, "agent": agent_id})
            }

        # Check for generated code block if Repair or Tutor
        complete_text = "".join(full_response)
        is_safe, extracted_code, sec_note = validate_ai_fix(complete_text, language=lang)

        yield {
            "event": "agent_done",
            "data": json.dumps({
                "is_done": True,
                "has_code": bool(extracted_code),
                "extracted_code": extracted_code,
                "is_safe": is_safe,
                "security_note": sec_note
            })
        }

    return EventSourceResponse(event_generator())


# =====================================================================
# AGENT PROMPT BUILDERS (WITH AST INJECTION)
# =====================================================================

def _build_detective_prompt(lang: str, code: str, error: str, query: str, ast_block: str) -> str:
    category, strategy = classify_error(error, language=lang)
    return f"""You are the Diagnostic Detective Agent in a multi-agent compiler platform.
Language: {lang.upper()}
Error Category: {category}
Teaching Strategy: {strategy}

--- SOURCE CODE ---
{code}

--- COMPILER / RUNTIME OUTPUT ---
{error}

{ast_block}

User Question: {query}

TASK:
1. Use the Abstract Syntax Tree (AST) above to pinpoint the exact failure line and scope.
2. If the parser flagged a syntax error in the AST, explain the exact token or delimiter issue immediately.
3. Formulate a crisp, technical diagnosis for the student.

Format as:
### FAULT LOCALIZATION
- Line / Scope: <line number or function/block from AST>
- Root Cause: <one sentence technical cause>

### TECHNICAL DIAGNOSIS
<2-3 concise bullet points explaining why the code failed>"""


def _build_repair_prompt(lang: str, code: str, error: str, query: str, ast_block: str) -> str:
    lang_tag = "python" if lang in ("python", "py") else ("java" if lang == "java" else "cpp")
    return f"""You are the Repair Agent in a multi-agent program repair platform.
Language: {lang.upper()}

--- BUGGY CODE ---
{code}

--- COMPILER / RUNTIME ERROR ---
{error}

{ast_block}

User Request: {query}

TASK:
Fix all compilation and runtime errors using the AST context to preserve defined functions, classes, and scopes.
DO NOT introduce any dangerous functions (system, popen, gets, strcpy, unsafe pointers, command injections).
Output the COMPLETE working code enclosed in ```{lang_tag} ... ``` code fences.

### REPAIR SUMMARY
(Brief 1-line note of what was changed)

### FIXED CODE
```{lang_tag}
(Complete corrected code here)
```"""


def _build_security_prompt(lang: str, code: str, error: str, query: str, ast_block: str) -> str:
    return f"""You are the Security Sentinel Agent.
Enforces 13-layer defense checking memory vulnerabilities, buffer overflows, process injection, format string bugs, and dangerous APIs.
Language: {lang.upper()}

--- SOURCE CODE ---
{code}

--- COMPILER / RUNTIME CONTEXT ---
{error}

{ast_block}

User Query: {query}

TASK:
Perform static security audit using the AST call expressions and symbols. Flag any CWE-119, CWE-78, buffer overflows, or unsanitized system calls.
Give a clear PASS / FAIL verdict with recommendations."""


def _build_tutor_prompt(lang: str, code: str, error: str, query: str, history: List[ChatMessage], ast_block: str) -> str:
    history_context = ""
    if len(history) > 1:
        history_context = "\nRecent Conversation:\n" + "\n".join(f"{m.role}: {m.content}" for m in history[-3:])

    return f"""You are the friendly Pedagogical Tutor Mentor in a programming education platform.
Language: {lang.upper()}

--- CURRENT CODE ---
```{lang}
{code}
```

--- OUTPUT / ERROR (if any) ---
{error}

{ast_block}
{history_context}

User's Latest Question: {query}

TASK:
Explain concepts clearly and encouragingly:
1. 💡 Conceptual Explanation: Explain why the compiler/runtime complained using the AST hierarchy.
2. 🔑 Core Invariant / Best Practice: What rule should the student remember?
3. ⚡ Complexity & Performance: Mention runtime or space complexity if applicable.
Keep it student-friendly and concise."""
