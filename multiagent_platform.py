"""
multiagent_platform.py - Collaborative Multi-Agent APR & Debugging Platform
Supports Llama 3, Microsoft Phi-3, and Alibaba Qwen models with specialized agent roles:
  1. DiagnosticAgent (Error Detective 🔍)
  2. RepairAgent (Code Architect 🛠️)
  3. SecurityAuditorAgent (Security Sentinel 🛡️ - Layer 2 & 12 Defense)
  4. TutorAgent (Pedagogical Mentor 🎓)
  5. MultiAgentOrchestrator (Swarm Coordinator & Multi-Model Council 🌐)
"""

import json
import os
import re
import time
import requests
from dataclasses import dataclass, field
from typing import Optional, Generator, Dict, Any, List

# Security & classification hooks from local architecture
from secure_scan import run_security_guardrail
from fix_engine import validate_ai_fix
from error_classifier import classify_error
from audit_logger import log_interaction
from security_logger import log_security_event

OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_GEN_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

# =====================================================================
# 1. MODEL REGISTRY & SUPPORT (Llama, Phi-3, Qwen)
# =====================================================================

MODEL_REGISTRY = {
    # --- Meta Llama Family ---
    "llama3.2:1b": {
        "family": "Llama",
        "name": "Llama 3.2 1B",
        "tag": "llama3.2:1b",
        "description": "⚡ Ultra-Fast 1B triage & quick debugging",
        "role_affinity": "DiagnosticAgent",
        "pull_cmd": "ollama pull llama3.2:1b"
    },
    "llama3:latest": {
        "family": "Llama",
        "name": "Llama 3 8B",
        "tag": "llama3:latest",
        "description": "🧠 Deep reasoning & comprehensive explanation",
        "role_affinity": "TutorAgent",
        "pull_cmd": "ollama pull llama3"
    },

    # --- Microsoft Phi-3 Family ---
    "phi3:mini": {
        "family": "Phi-3",
        "name": "Phi-3 Mini 3.8B",
        "tag": "phi3:mini",
        "description": "🔬 Microsoft 3.8B high-density logical reasoning",
        "role_affinity": "DiagnosticAgent",
        "pull_cmd": "ollama pull phi3:mini"
    },
    "phi3:medium": {
        "family": "Phi-3",
        "name": "Phi-3 Medium 14B",
        "tag": "phi3:medium",
        "description": "🏛️ Microsoft 14B high-capacity instruction follower",
        "role_affinity": "TutorAgent",
        "pull_cmd": "ollama pull phi3:medium"
    },

    # --- Alibaba Qwen Family ---
    "qwen2.5:coder": {
        "family": "Qwen",
        "name": "Qwen 2.5 Coder 7B",
        "tag": "qwen2.5:coder",
        "description": "💻 Alibaba SOTA code synthesis & bug fixing",
        "role_affinity": "RepairAgent",
        "pull_cmd": "ollama pull qwen2.5:coder"
    },
    "qwen2.5-coder:1.5b": {
        "family": "Qwen",
        "name": "Qwen 2.5 Coder 1.5B",
        "tag": "qwen2.5-coder:1.5b",
        "description": "⚡ Ultra-fast specialized coding model",
        "role_affinity": "RepairAgent",
        "pull_cmd": "ollama pull qwen2.5-coder:1.5b"
    },
    "qwen2.5:latest": {
        "family": "Qwen",
        "name": "Qwen 2.5 7B",
        "tag": "qwen2.5:latest",
        "description": "🌐 Alibaba general multilingual reasoning",
        "role_affinity": "TutorAgent",
        "pull_cmd": "ollama pull qwen2.5"
    }
}

DEFAULT_FAMILY_MODELS = {
    "Llama": "llama3.2:1b",
    "Phi-3": "phi3:mini",
    "Qwen": "qwen2.5:coder"
}

def is_ollama_online(timeout: float = 1.5) -> bool:
    """Quick ping to check if the Ollama service is reachable."""
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False

def get_installed_ollama_models() -> List[str]:
    """Retrieves list of locally pulled Ollama models."""
    try:
        r = requests.get(OLLAMA_TAGS_URL, timeout=2.0)
        if r.status_code == 200:
            return [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]
    except Exception:
        pass
    return []

def resolve_model_alias(model_tag: str) -> str:
    """Resolves partial names like 'phi3', 'qwen', or 'llama3' to registered tags."""
    tag_clean = model_tag.lower().strip()
    if tag_clean in MODEL_REGISTRY:
        return tag_clean
    for key, data in MODEL_REGISTRY.items():
        if tag_clean == data["name"].lower() or tag_clean == data["family"].lower():
            return key
        if tag_clean in key:
            return key
    return tag_clean

def query_ollama(prompt: str, model_tag: str, temperature: float = 0.2, num_predict: int = 500, stream: bool = False, timeout: int = 60) -> Any:
    """Direct query to Ollama endpoint with fallback warning if offline."""
    if not is_ollama_online():
        raise ConnectionError(
            f"Ollama is offline. Start it with 'ollama serve' and ensure model '{model_tag}' is available."
        )

    payload = {
        "model": model_tag,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict
        }
    }
    r = requests.post(OLLAMA_GEN_URL, json=payload, stream=stream, timeout=(5, timeout))
    if r.status_code != 200:
        raise RuntimeError(f"Ollama returned HTTP {r.status_code}: {r.text}")

    if stream:
        return r.iter_lines()
    else:
        # Aggregate full response
        data = r.json()
        return data.get("response", "")

# =====================================================================
# 2. DATA STRUCTURES FOR MULTI-AGENT COLLABORATION
# =====================================================================

@dataclass
class AgentMessage:
    agent_name: str
    role: str
    model: str
    status: str  # "success", "warning", "rejected", "approved"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MultiAgentPlan:
    language: str
    original_code: str
    error_output: str
    execution_mode: str  # "swarm" or "council"
    diagnostic_report: Optional[AgentMessage] = None
    repair_proposal: Optional[AgentMessage] = None
    security_verdict: Optional[AgentMessage] = None
    tutor_feedback: Optional[AgentMessage] = None
    council_proposals: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    final_code: Optional[str] = None
    is_secure: bool = False
    all_messages: List[AgentMessage] = field(default_factory=list)

# =====================================================================
# 3. SPECIALIZED AGENTS
# =====================================================================

class BaseAgent:
    def __init__(self, name: str, role: str, default_model: str):
        self.name = name
        self.role = role
        self.default_model = default_model

    def call_model(self, prompt: str, model_override: Optional[str] = None, temperature: float = 0.2) -> str:
        model = model_override or self.default_model
        try:
            return query_ollama(prompt, model, temperature=temperature)
        except Exception as e:
            # Generate deterministic fallback simulation for testing or offline environments
            return self._offline_simulation(prompt, str(e))

    def _offline_simulation(self, prompt: str, error_msg: str) -> str:
        return f"[Agent Offline Simulator - {self.name}] Notice: Ollama request unreachable ({error_msg})."

class DiagnosticAgent(BaseAgent):
    """
    🔍 Detective Agent:
    Specialized in pinpointing compiler errors, syntax faults, and runtime crashes.
    """
    def __init__(self, default_model: str = "phi3:mini"):
        super().__init__("Diagnostic Agent", "Error Detective 🔍", default_model)

    def _offline_simulation(self, prompt: str, error_msg: str) -> str:
        return """### FAULT LOCALIZATION
- Line / Construct: Compiler / Runtime Error Output
- Root Cause: Syntax or logic violation flagged by execution engine.

### TECHNICAL DIAGNOSIS
- Missing expected token, delimiter, or unhandled exception.
- Program interrupted before completing execution successfully.
- Verify bounds and grammar rules for the active language."""

    def diagnose(self, code: str, error: str, language: str = "cpp", model_override: Optional[str] = None) -> AgentMessage:
        t0 = time.time()
        category, strategy = classify_error(error, language=language)
        
        prompt = f"""You are the Diagnostic Agent in a secure multi-agent compiler platform.
Language: {language.upper()}
Error Category: {category}
Teaching Strategy: {strategy}

--- SOURCE CODE ---
{code}

--- COMPILER / RUNTIME OUTPUT ---
{error}

TASK:
1. Identify the exact line number(s) and syntax/semantic cause of each failure.
2. Formulate a crisp, technical diagnosis for the Repair Agent.
3. Keep it concise, structured, and free of conversational filler.

Format as:
### FAULT LOCALIZATION
- Line / Construct: <line number or function>
- Root Cause: <one sentence description>

### TECHNICAL DIAGNOSIS
<2-3 concise bullet points explaining why the compiler or runtime failed>"""

        response = self.call_model(prompt, model_override=model_override, temperature=0.1)
        latency = round(time.time() - t0, 3)

        return AgentMessage(
            agent_name=self.name,
            role=self.role,
            model=model_override or self.default_model,
            status="success",
            content=response,
            metadata={
                "category": category,
                "strategy": strategy,
                "latency_sec": latency
            }
        )

class RepairAgent(BaseAgent):
    """
    🛠️ Code Architect:
    Synthesizes minimal, idiomatic, and bug-free code patches.
    """
    def __init__(self, default_model: str = "qwen2.5:coder"):
        super().__init__("Repair Agent", "Code Architect 🛠️", default_model)

    def synthesize_repair(
        self,
        code: str,
        error: str,
        diagnosis: str,
        language: str = "cpp",
        critique: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> AgentMessage:
        t0 = time.time()
        lang_tag = "python" if language.lower() in ("python", "py") else ("java" if language.lower() == "java" else "cpp")

        critique_block = ""
        if critique:
            critique_block = f"""
CRITICAL SECURITY / BUG CORRECTION FROM AUDITOR:
Your previous fix was REJECTED: {critique}
You MUST address this flaw and make the code 100% secure and compilable.
"""

        prompt = f"""You are the Repair Agent in a multi-agent program repair platform.
Language: {language.upper()}

--- BUGGY CODE ---
{code}

--- COMPILER / RUNTIME ERROR ---
{error}

--- DIAGNOSTIC AGENT REPORT ---
{diagnosis}
{critique_block}
TASK:
Fix all compilation and runtime errors.
Preserve the user's original logic, variable naming, and style.
DO NOT introduce any dangerous functions (system, popen, gets, strcpy, unsafe pointers, command injections).
Output the COMPLETE working code enclosed in ```{lang_tag} ... ``` code fences.

### REPAIR SUMMARY
(Brief 1-line note of what was changed)

### FIXED CODE
```{lang_tag}
(Complete corrected code here)
```"""

        response = self.call_model(prompt, model_override=model_override, temperature=0.2)
        latency = round(time.time() - t0, 3)

        # Extract code block
        is_safe, extracted_code, sec_note = validate_ai_fix(response, language=language)

        return AgentMessage(
            agent_name=self.name,
            role=self.role,
            model=model_override or self.default_model,
            status="success" if extracted_code else "warning",
            content=response,
            metadata={
                "extracted_code": extracted_code,
                "latency_sec": latency,
                "pre_scan_note": sec_note
            }
        )

class SecurityAuditorAgent(BaseAgent):
    """
    🛡️ Sentinel Guard:
    Enforces Layer 2 (Static Scanner) & Layer 12 (AI Fix Verification).
    Intercepts vulnerabilities and triggers iterative repair if violations exist.
    """
    def __init__(self, default_model: str = "llama3.2:1b"):
        super().__init__("Security Auditor Agent", "Security Sentinel 🛡️", default_model)

    def audit(self, proposed_code: Optional[str], raw_response: str, language: str = "cpp") -> AgentMessage:
        t0 = time.time()
        if not proposed_code:
            return AgentMessage(
                agent_name=self.name,
                role=self.role,
                model=self.default_model,
                status="rejected",
                content="❌ Security Audit Failed: No valid code block found in Repair proposal.",
                metadata={"is_secure": False, "reason": "Missing code block"}
            )

        # 1. Run 13-Layer static security scanner
        is_hard_blocked, block_msg, soft_warnings = run_security_guardrail(proposed_code, language=language)
        latency = round(time.time() - t0, 3)

        if is_hard_blocked:
            log_security_event("MULTIAGENT_FIX_REJECTED", "CRITICAL", block_msg, proposed_code, language=language)
            return AgentMessage(
                agent_name=self.name,
                role=self.role,
                model=self.default_model,
                status="rejected",
                content=f"🚫 SECURITY GUARDRAIL TRIGGERED:\n{block_msg}\nThe fix was rejected and sent back to Repair Agent for remediation.",
                metadata={
                    "is_secure": False,
                    "violation": block_msg,
                    "soft_warnings": soft_warnings,
                    "latency_sec": latency
                }
            )

        # Approved
        advisory = " All security checks passed."
        if soft_warnings:
            advisory = " Passed with advisories: " + " | ".join(soft_warnings)

        return AgentMessage(
            agent_name=self.name,
            role=self.role,
            model=self.default_model,
            status="approved",
            content=f"✅ Security Audit PASSED.{advisory}\nVerified against OWASP, CWE-119, and Process Injection standards.",
            metadata={
                "is_secure": True,
                "soft_warnings": soft_warnings,
                "latency_sec": latency
            }
        )

class TutorAgent(BaseAgent):
    """
    🎓 Pedagogical Mentor:
    Explains the bug, underlying concept, algorithmic complexity, and prevention tips.
    """
    def __init__(self, default_model: str = "phi3:mini"):
        super().__init__("Tutor Agent", "Pedagogical Mentor 🎓", default_model)

    def teach(
        self,
        language: str,
        buggy_code: str,
        diagnosis: str,
        fixed_code: Optional[str],
        model_override: Optional[str] = None
    ) -> AgentMessage:
        t0 = time.time()
        prompt = f"""You are the Tutor Agent in an educational programming platform.
Language: {language.upper()}

--- ORIGINAL BUGGY CODE ---
{buggy_code}

--- DIAGNOSTIC FINDINGS ---
{diagnosis}

--- VERIFIED FIX ---
{fixed_code or 'See above'}

TASK:
Provide an encouraging, clear pedagogical lesson for a computer science student:
1. 💡 Conceptual Explanation: Explain *why* the compiler complained in intuitive terms.
2. 🔑 Key Rule / Best Practice: What core language invariant must the student remember?
3. ⚡ Complexity & Performance: Mention if the fix affects runtime or memory.
Keep it concise, friendly, and structured."""

        response = self.call_model(prompt, model_override=model_override, temperature=0.3)
        latency = round(time.time() - t0, 3)

        return AgentMessage(
            agent_name=self.name,
            role=self.role,
            model=model_override or self.default_model,
            status="success",
            content=response,
            metadata={"latency_sec": latency}
        )

# =====================================================================
# 4. MULTI-AGENT ORCHESTRATOR & COUNCIL
# =====================================================================

class MultiAgentOrchestrator:
    """
    Orchestrates collaboration among agents and supports:
      - Swarm Pipeline (Detective -> Architect -> Sentinel -> Mentor)
      - Multi-Model Council (Llama vs Phi-3 vs Qwen)
      - Dynamic model assignment per agent
    """
    def __init__(
        self,
        diagnostic_model: str = "phi3:mini",
        repair_model: str = "qwen2.5:coder",
        security_model: str = "llama3.2:1b",
        tutor_model: str = "phi3:mini"
    ):
        self.diagnostic_agent = DiagnosticAgent(default_model=diagnostic_model)
        self.repair_agent = RepairAgent(default_model=repair_model)
        self.security_agent = SecurityAuditorAgent(default_model=security_model)
        self.tutor_agent = TutorAgent(default_model=tutor_model)

    def run_collaborative_swarm(
        self,
        code: str,
        error: str,
        language: str = "cpp",
        model_overrides: Optional[Dict[str, str]] = None,
        max_repair_attempts: int = 2
    ) -> MultiAgentPlan:
        """
        Executes autonomous multi-agent pipeline with security feedback loop.
        """
        overrides = model_overrides or {}
        diag_mod = overrides.get("diagnostic", self.diagnostic_agent.default_model)
        rep_mod = overrides.get("repair", self.repair_agent.default_model)
        tutor_mod = overrides.get("tutor", self.tutor_agent.default_model)

        plan = MultiAgentPlan(
            language=language,
            original_code=code,
            error_output=error,
            execution_mode="swarm"
        )

        # Step 1: Detective Diagnosis
        diag_msg = self.diagnostic_agent.diagnose(code, error, language=language, model_override=diag_mod)
        plan.diagnostic_report = diag_msg
        plan.all_messages.append(diag_msg)

        # Step 2 & 3: Architect Synthesis & Sentinel Security Audit (Feedback loop)
        critique = None
        attempt = 0
        final_code = None
        is_secure = False

        while attempt < max_repair_attempts:
            attempt += 1
            repair_msg = self.repair_agent.synthesize_repair(
                code=code,
                error=error,
                diagnosis=diag_msg.content,
                language=language,
                critique=critique,
                model_override=rep_mod
            )
            plan.repair_proposal = repair_msg
            plan.all_messages.append(repair_msg)

            candidate_code = repair_msg.metadata.get("extracted_code")
            sec_msg = self.security_agent.audit(candidate_code, repair_msg.content, language=language)
            plan.security_verdict = sec_msg
            plan.all_messages.append(sec_msg)

            if sec_msg.status == "approved" and candidate_code:
                final_code = candidate_code
                is_secure = True
                break
            else:
                critique = sec_msg.content

        plan.final_code = final_code or repair_msg.metadata.get("extracted_code")
        plan.is_secure = is_secure

        # Step 4: Pedagogical Mentorship
        tutor_msg = self.tutor_agent.teach(
            language=language,
            buggy_code=code,
            diagnosis=diag_msg.content,
            fixed_code=plan.final_code,
            model_override=tutor_mod
        )
        plan.tutor_feedback = tutor_msg
        plan.all_messages.append(tutor_msg)

        # Audit logging
        log_interaction(
            user_prompt=f"Multi-Agent Swarm ({language.upper()})",
            llm_response=f"Diagnosis:\n{diag_msg.content}\n\nFix:\n{plan.final_code}\n\nLesson:\n{tutor_msg.content}",
            code_snippet=code,
            error_category=diag_msg.metadata.get("category", "MultiAgent Analysis"),
            fixed_code=plan.final_code or "N/A"
        )

        return plan

    def run_multi_model_council(
        self,
        code: str,
        error: str,
        language: str = "cpp",
        council_models: Optional[Dict[str, str]] = None
    ) -> MultiAgentPlan:
        """
        Multi-Model Council: Solves the bug with Llama, Phi-3, and Qwen models,
        auditing each proposal to compare results side-by-side.
        """
        targets = council_models or {
            "Meta Llama 3": "llama3.2:1b",
            "Microsoft Phi-3": "phi3:mini",
            "Alibaba Qwen": "qwen2.5:coder"
        }

        plan = MultiAgentPlan(
            language=language,
            original_code=code,
            error_output=error,
            execution_mode="council"
        )

        # Step 1: Base diagnostic
        diag_msg = self.diagnostic_agent.diagnose(code, error, language=language)
        plan.diagnostic_report = diag_msg
        plan.all_messages.append(diag_msg)

        # Step 2: Query each model for repair & audit
        council_results = {}
        best_code = None

        for family_name, model_tag in targets.items():
            rep_msg = self.repair_agent.synthesize_repair(
                code=code,
                error=error,
                diagnosis=diag_msg.content,
                language=language,
                model_override=model_tag
            )
            candidate_code = rep_msg.metadata.get("extracted_code")
            sec_msg = self.security_agent.audit(candidate_code, rep_msg.content, language=language)

            council_results[family_name] = {
                "model": model_tag,
                "repair": rep_msg,
                "audit": sec_msg,
                "extracted_code": candidate_code,
                "is_secure": sec_msg.status == "approved"
            }

            if sec_msg.status == "approved" and candidate_code and not best_code:
                best_code = candidate_code

        plan.council_proposals = council_results
        plan.final_code = best_code or next(
            (res["extracted_code"] for res in council_results.values() if res["extracted_code"]), None
        )
        plan.is_secure = any(res["is_secure"] for res in council_results.values())

        # Step 3: Tutor synthesizes council takeaway
        tutor_msg = self.tutor_agent.teach(
            language=language,
            buggy_code=code,
            diagnosis=diag_msg.content,
            fixed_code=plan.final_code
        )
        plan.tutor_feedback = tutor_msg
        plan.all_messages.append(tutor_msg)

        return plan
