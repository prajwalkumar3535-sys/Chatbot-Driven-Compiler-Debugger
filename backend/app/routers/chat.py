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
                formatted_council_code = _format_code_for_prompt(code, error)
                council_prompt = f"""You are participating in the Multi-Model Program Repair Council.
Language: {lang.upper()}

Original Source Code:
```{lang_tag}
{formatted_council_code}
```

Compiler / Runtime Output:
{error}

{ast_block}

User Query: {user_query}

STRICT INSTRUCTIONS:
- Be direct and concise. NO conversational filler, greetings, or sign-offs (no 'Hello', 'Certainly', 'Sure').
- Only state the necessary root cause and solution.
- Provide complete, working, compile-ready fixed code enclosed in ```{lang_tag} ... ``` code block so the user can apply it directly to the editor.

### DIAGNOSIS
- Cause: <concise root cause>

### FIXED CODE
```{lang_tag}
<complete corrected code>
```"""

                model_text = []
                async for token in stream_ollama_response(council_prompt, model=mod, temperature=0.2):
                    model_text.append(token)
                    yield {
                        "event": "token",
                        "data": json.dumps({"model": name, "token": token})
                    }

                full_text = "".join(model_text)
                is_safe, extracted, sec_note = validate_ai_fix(full_text, language=lang, original_code=code)
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

        # Check for generated code block and reconstruct full 5,000+ line code if applicable
        complete_text = "".join(full_response)
        is_safe, extracted_code, sec_note = validate_ai_fix(complete_text, language=lang, original_code=code)

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
# AGENT PROMPT BUILDERS (WITH AST INJECTION & 5000+ LINE SPLICER)
# =====================================================================

def _format_code_for_prompt(code: str, error: str) -> str:
    total_lines = len(code.splitlines())
    if total_lines <= 250:
        return code

    lines = code.splitlines()
    err_line_match = re.search(r'(?:line\s+|:\s*)(\d+)(?::|\s|,|$)', error, re.IGNORECASE)
    if err_line_match:
        try:
            target_line = int(err_line_match.group(1))
            start_line = max(0, target_line - 35)
            end_line = min(len(lines), target_line + 35)
            window = "\n".join(lines[start_line:end_line])
            return f"""// [NOTE: Massive codebase ({total_lines} total lines). Showing lines {start_line+1} to {end_line} around the failure point:]
{window}
// [The AST Splicer will automatically merge your fixed function/block into the complete {total_lines}-line codebase]"""
        except Exception:
            pass

    return f"""// [NOTE: Massive codebase ({total_lines} total lines). Showing head and tail:]
{"\n".join(lines[:100])}
// ... [{total_lines - 150} lines omitted for focus - AST Splicer will reconstruct full file] ...
{"\n".join(lines[-50:])}"""


def _build_detective_prompt(lang: str, code: str, error: str, query: str, ast_block: str) -> str:
    lang_tag = "python" if lang in ("python", "py") else ("java" if lang == "java" else "cpp")
    category, strategy = classify_error(error, language=lang)
    formatted_code = _format_code_for_prompt(code, error)
    total_lines = len(code.splitlines())
    large_note = f"\n- Large codebase detected ({total_lines} lines). Output the corrected function/scope in ```{lang_tag} ... ```; AST Splicer will merge it into the full file." if total_lines > 250 else ""

    return f"""You are the Detective Agent.
Language: {lang.upper()}
Category: {category}

--- SOURCE CODE ---
{formatted_code}

--- COMPILER / RUNTIME OUTPUT ---
{error}

{ast_block}

User Question: {query}

STRICT INSTRUCTIONS:
- Be direct, technical, and concise.
- NO conversational filler, greetings, or pleasantries (no 'Hello', 'Certainly', 'Sure').
- Only state the exact failure point and the root cause.{large_note}
- If providing or suggesting fixed code, enclose complete working code in ```{lang_tag} ... ``` code block.

### FAULT LOCALIZATION
- Line / Scope: <line number or function from AST>
- Root Cause: <one sentence technical cause>

### DIAGNOSIS
<2-3 concise bullet points explaining why the code failed>

```{lang_tag}
<complete corrected code if fix is suggested>
```"""


def _build_repair_prompt(lang: str, code: str, error: str, query: str, ast_block: str) -> str:
    lang_tag = "python" if lang in ("python", "py") else ("java" if lang == "java" else "cpp")
    formatted_code = _format_code_for_prompt(code, error)
    total_lines = len(code.splitlines())
    large_note = f"\n- Large codebase detected ({total_lines} lines). Output the complete corrected function/scope in ```{lang_tag} ... ```; AST Splicer will merge it into the full {total_lines}-line file." if total_lines > 250 else ""

    return f"""You are the Repair Agent.
Language: {lang.upper()}

--- BUGGY CODE ---
{formatted_code}

--- COMPILER / RUNTIME ERROR ---
{error}

{ast_block}

User Request: {query}

STRICT INSTRUCTIONS:
- Be concise and direct. Do NOT write conversational filler, greetings, or apologies.
- Only state the needy information: what was broken and the fix.{large_note}
- Output the COMPLETE working code enclosed in ```{lang_tag} ... ``` markdown fences so it renders in the code box with the Apply to Editor button.

### SUMMARY OF FIX
- <1-2 bullet points explaining what was fixed>

### FIXED CODE
```{lang_tag}
<complete corrected compilable code here>
```"""


def _build_security_prompt(lang: str, code: str, error: str, query: str, ast_block: str) -> str:
    lang_tag = "python" if lang in ("python", "py") else ("java" if lang == "java" else "cpp")
    formatted_code = _format_code_for_prompt(code, error)
    return f"""You are the Security Sentinel Agent.
Enforces 13-layer defense against memory vulnerabilities, buffer overflows, process injections, and dangerous APIs.
Language: {lang.upper()}

--- SOURCE CODE ---
{formatted_code}

--- COMPILER / RUNTIME CONTEXT ---
{error}

{ast_block}

User Query: {query}

STRICT INSTRUCTIONS:
- Be direct, factual, and concise. NO conversational filler.
- State whether the code is PASS, WARNING, or BLOCKED.
- If vulnerabilities exist, provide the secured code enclosed in ```{lang_tag} ... ``` code block.

### SECURITY VERDICT
- Status: <PASS / WARNING / BLOCKED>
- Risk Analysis: <1-2 concise bullet points>

```{lang_tag}
<secure corrected code if remediation is needed>
```"""


def _build_tutor_prompt(lang: str, code: str, error: str, query: str, history: List[ChatMessage], ast_block: str) -> str:
    lang_tag = "python" if lang in ("python", "py") else ("java" if lang == "java" else "cpp")
    formatted_code = _format_code_for_prompt(code, error)
    total_lines = len(code.splitlines())
    large_note = f"\n- Large codebase ({total_lines} lines). Enclose the fixed function/block in ```{lang_tag} ... ```; AST Splicer will merge it into the full file." if total_lines > 250 else ""

    history_context = ""
    if len(history) > 1:
        history_context = "\nRecent Conversation:\n" + "\n".join(f"{m.role}: {m.content}" for m in history[-3:])

    return f"""You are the Tutor Mentor.
Language: {lang.upper()}

--- CURRENT CODE ---
```{lang_tag}
{formatted_code}
```

--- OUTPUT / ERROR ---
{error}

{ast_block}
{history_context}

User Question: {query}

STRICT INSTRUCTIONS:
- Be direct, concise, and focused. Only explain the necessary concepts without conversational filler (no 'Hello', 'Certainly', 'Sure!', 'Let us take a look').
- Only explain the needy things: why the code failed and the invariant to remember.{large_note}
- ALWAYS enclose the complete corrected code in a ```{lang_tag} ... ``` markdown code block so the student can apply it to the editor with one click.

### EXPLANATION
- 💡 Root Cause: <concise explanation of the error using AST context>
- 🔑 Core Invariant: <the rule or best practice to remember>

### FIXED CODE
```{lang_tag}
<complete corrected working code>
```"""
