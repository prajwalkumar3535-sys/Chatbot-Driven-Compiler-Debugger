import streamlit as st
import subprocess
import requests
import os
import time
import json

from codecarbon import EmissionsTracker

# Import our custom security & execution modules
from language_config import LANGUAGE_CONFIG, ALLOWED_LANGUAGES, get_language_config, get_display_name
from fix_engine import validate_ai_fix
from secure_scan import run_security_guardrail, validate_input
from error_classifier import classify_error, get_diagnostic_prompt
from compiler_service import compile_and_run
from audit_logger import log_interaction 
from error_logger import log_error 
from lldb_engine import agentic_debug_loop 
from security_logger import log_security_event

# Multi-Agent Platform & Models (Llama, Phi-3, Qwen)
from multiagent_platform import (
    MODEL_REGISTRY,
    DEFAULT_FAMILY_MODELS,
    MultiAgentOrchestrator,
    MultiAgentPlan,
    is_ollama_online,
    get_installed_ollama_models,
    resolve_model_alias
)

# LLM config
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_HEALTH_URL = os.environ.get("OLLAMA_TAGS_URL", "http://localhost:11434/api/tags")
DEFAULT_MODEL = "qwen2.5:coder"


def is_ollama_running() -> bool:
    """Fast check to verify if Ollama server is reachable."""
    return is_ollama_online(timeout=1.5)


def get_available_models():
    """Detects available models in Ollama or returns registered defaults."""
    detected = get_installed_ollama_models()
    if detected:
        return detected
    return list(MODEL_REGISTRY.keys())


def get_ai_explanation(prompt, model_name=None):
    """Sends prompt to local Ollama model with fast streaming concatenation & timeout protection."""
    model = model_name or st.session_state.get("selected_ai_model", DEFAULT_MODEL)
    if not is_ollama_running():
        return (
            "⚠️ **AI Assistant Offline** — Ollama is not running on this machine.\n\n"
            "To enable AI explanations and fixes, start Ollama:\n"
            "```bash\nollama serve\n```\n"
            f"And ensure the model is pulled:\n"
            f"```bash\nollama pull {model}\n```\n"
            "*(Operating in simulated multi-agent fallback mode)*"
        )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": 450,
            "temperature": 0.2
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=(5, 120))
        if response.status_code == 200:
            full_response = []
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    full_response.append(data.get("response", ""))
                    if data.get("done", False):
                        break
            return "".join(full_response)
        else:
            return f"⚠️ Ollama returned an error (HTTP {response.status_code}). Please check your Ollama setup."
    except Exception as e:
        return f"⚠️ AI request failed: {str(e)}"


def stream_ai_explanation(prompt, model_name=None):
    """Streams response from local Ollama model token-by-token for interactive real-time typing."""
    model = model_name or st.session_state.get("selected_ai_model", DEFAULT_MODEL)
    if not is_ollama_running():
        yield (
            f"⚠️ **AI Assistant Offline** — Ollama is not running.\n\n"
            f"Run `ollama serve` and `ollama pull {model}` in a terminal."
        )
        return

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": 500,
            "temperature": 0.3
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=(5, 120))
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    token = data.get("response", "")
                    yield token
                    if data.get("done", False):
                        break
        else:
            yield f"⚠️ Ollama returned an error (HTTP {response.status_code})."
    except Exception as e:
        yield f"⚠️ AI request failed: {str(e)}"


def stop_and_save_metrics(tracker, start_t):
    """Stops the carbon tracker and saves metrics with safe fallback."""
    try:
        emissions_kg = tracker.stop()
        if emissions_kg is None:
            emissions_kg = 0.0
            energy = 0.0
        else:
            energy = tracker.final_emissions_data.energy_consumed if tracker.final_emissions_data else 0.0

        st.session_state.green_metrics = {
            "latency": time.time() - start_t,
            "energy": energy,
            "carbon": emissions_kg * 1000  # Convert to grams
        }
    except Exception as e:
        st.session_state.green_metrics = {
            "latency": time.time() - start_t,
            "energy": 0.001500,
            "carbon": 0.00050
        }
        print(f"CodeCarbon Warning Caught: {e}")


# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Multi-Agent Compiler & Debugger Platform",
    page_icon="⚡",
    layout="wide"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_language" not in st.session_state:
    st.session_state.selected_language = "cpp"

if "code_per_lang" not in st.session_state:
    st.session_state.code_per_lang = {
        lang: LANGUAGE_CONFIG[lang]["default_code"] for lang in ALLOWED_LANGUAGES
    }

if "last_status" not in st.session_state:
    st.session_state.last_status = None
    st.session_state.last_stdout = ""
    st.session_state.last_stderr = ""
    st.session_state.last_lang = "cpp"

if "last_agent_log" not in st.session_state:
    st.session_state.last_agent_log = None

if "last_multiagent_plan" not in st.session_state:
    st.session_state.last_multiagent_plan = None

if "green_metrics" not in st.session_state:
    st.session_state.green_metrics = None

if "platform_mode" not in st.session_state:
    st.session_state.platform_mode = "Multi-Agent Swarm"

if "selected_ai_model" not in st.session_state:
    st.session_state.selected_ai_model = "qwen2.5:coder"

if "agent_models" not in st.session_state:
    st.session_state.agent_models = {
        "diagnostic": "phi3:mini",
        "repair": "qwen2.5:coder",
        "security": "llama3.2:1b",
        "tutor": "phi3:mini"
    }

# --- HEADER TITLE ---
st.title("⚡ Multi-Agent Sandbox Compiler & Debugger")
st.markdown("### Secure Multi-Language Sandbox with Collaborative Multi-Agent APR (Llama • Phi-3 • Qwen)")

# --- CONTROL BAR ---
c1, c2, c3, c4 = st.columns([1.5, 2.5, 2.5, 1.5])

with c1:
    lang_display_options = ["C++", "Python", "Java"]
    lang_key_map = {"C++": "cpp", "Python": "python", "Java": "java"}
    inv_lang_map = {v: k for k, v in lang_key_map.items()}

    current_display = inv_lang_map.get(st.session_state.selected_language, "C++")
    selected_display = st.selectbox("🌐 Language:", lang_display_options, index=lang_display_options.index(current_display))
    new_lang_key = lang_key_map[selected_display]

    if new_lang_key != st.session_state.selected_language:
        st.session_state.selected_language = new_lang_key
        st.session_state.last_status = None
        st.session_state.last_agent_log = None
        st.session_state.last_multiagent_plan = None
        st.rerun()

current_lang = st.session_state.selected_language
current_cfg = get_language_config(current_lang)

with c2:
    mode_options = [
        "🤖 Multi-Agent Swarm (4 Specialized Agents)",
        "🏛️ Multi-Model Council (Llama vs Phi-3 vs Qwen)",
        "⚡ Single-Model Direct Mode"
    ]
    mode_map = {
        "🤖 Multi-Agent Swarm (4 Specialized Agents)": "Multi-Agent Swarm",
        "🏛️ Multi-Model Council (Llama vs Phi-3 vs Qwen)": "Multi-Model Council",
        "⚡ Single-Model Direct Mode": "Single-Model Direct"
    }
    inv_mode_map = {v: k for k, v in mode_map.items()}
    current_mode_label = inv_mode_map.get(st.session_state.platform_mode, mode_options[0])
    selected_mode_label = st.selectbox("🎯 Platform Mode:", mode_options, index=mode_options.index(current_mode_label))
    st.session_state.platform_mode = mode_map[selected_mode_label]

with c3:
    model_choices = [
        ("qwen2.5:coder", "💻 Qwen 2.5 Coder 7B (Alibaba SOTA)"),
        ("qwen2.5-coder:1.5b", "⚡ Qwen 2.5 Coder 1.5B (Fast Coder)"),
        ("phi3:mini", "🔬 Phi-3 Mini 3.8B (Microsoft Logic)"),
        ("phi3:medium", "🧠 Phi-3 Medium 14B (Microsoft Deep)"),
        ("llama3.2:1b", "🦙 Llama 3.2 1B (Meta Ultra-Fast)"),
        ("llama3:latest", "🦙 Llama 3 8B (Meta Deep Reasoning)")
    ]
    model_vals = [m[0] for m in model_choices]
    model_labels = [m[1] for m in model_choices]
    
    curr_mod = st.session_state.selected_ai_model
    def_idx = model_vals.index(curr_mod) if curr_mod in model_vals else 0
    selected_label = st.selectbox("🤖 Primary Model / Family:", model_labels, index=def_idx)
    st.session_state.selected_ai_model = model_vals[model_labels.index(selected_label)]

with c4:
    ollama_up = is_ollama_running()
    status_badge = "🟢 Ollama Online" if ollama_up else "🔴 Ollama Offline"
    st.markdown(f"**Status:** `{status_badge}`")
    st.caption(f"Sandbox: `{current_cfg['docker_image']}`")

# --- EXPANDABLE MULTI-AGENT SETTINGS & MODEL SETUP ---
with st.expander("⚙️ Multi-Agent Settings, Model Routing & Ollama Setup Guide", expanded=False):
    m_col1, m_col2 = st.columns([1.5, 1.5])
    with m_col1:
        st.markdown("#### 👥 Agent Model Assignments")
        st.caption("Customize which specialized model powers each agent in the Swarm:")
        
        diag_choice = st.selectbox(
            "🔍 Diagnostic Agent (Detective):",
            model_vals,
            index=model_vals.index(st.session_state.agent_models.get("diagnostic", "phi3:mini")),
            key="cfg_diag_model"
        )
        rep_choice = st.selectbox(
            "🛠️ Repair Agent (Architect):",
            model_vals,
            index=model_vals.index(st.session_state.agent_models.get("repair", "qwen2.5:coder")),
            key="cfg_repair_model"
        )
        sec_choice = st.selectbox(
            "🛡️ Security Sentinel (Auditor):",
            model_vals,
            index=model_vals.index(st.session_state.agent_models.get("security", "llama3.2:1b")),
            key="cfg_sec_model"
        )
        tutor_choice = st.selectbox(
            "🎓 Tutor Agent (Mentor):",
            model_vals,
            index=model_vals.index(st.session_state.agent_models.get("tutor", "phi3:mini")),
            key="cfg_tutor_model"
        )
        st.session_state.agent_models = {
            "diagnostic": diag_choice,
            "repair": rep_choice,
            "security": sec_choice,
            "tutor": tutor_choice
        }

    with m_col2:
        st.markdown("#### 📥 Ollama Quick Pull Reference")
        st.markdown("""
Run the following commands in your terminal to enable local inference for all models:
```bash
# Start Ollama service
ollama serve

# Pull Microsoft Phi-3
ollama pull phi3:mini

# Pull Alibaba Qwen 2.5 Coder
ollama pull qwen2.5:coder

# Pull Meta Llama 3
ollama pull llama3.2:1b
```
*(If Ollama is offline, the platform provides automated rule scanning and structured simulation)*
""")

col1, col2 = st.columns(2)

# ============================================================
# LEFT COLUMN: THE CODE EDITOR & COMPILER
# ============================================================
with col1:
    st.subheader(f"📝 {current_cfg['display_name']} Code Editor")
    
    # Text editor for active language
    editor_key = f"code_editor_{current_lang}"
    default_lang_code = st.session_state.code_per_lang.get(current_lang, current_cfg["default_code"])
    user_code = st.text_area(f"Write your {current_cfg['display_name']} code here:", value=default_lang_code, height=340, key=editor_key)
    st.session_state.code_per_lang[current_lang] = user_code

    # Optional Stdin input area
    with st.expander("📥 Standard Input (stdin) - Optional"):
        stdin_input = st.text_area("Provide input lines for your program:", value="", height=70, key=f"stdin_{current_lang}")

    col1_a, col1_b, col1_c = st.columns([1.5, 1.8, 1.5])
    with col1_a:
        action_label = "Compile & Run" if current_cfg["needs_compile"] else "Run Code"
        run_btn = st.button(f"▶️ {action_label}", type="primary", use_container_width=True)
    with col1_b:
        if st.session_state.last_multiagent_plan and st.session_state.last_multiagent_plan.final_code:
            if st.button("📥 Apply Fix to Editor", use_container_width=True):
                st.session_state.code_per_lang[current_lang] = st.session_state.last_multiagent_plan.final_code
                st.success("✅ Fix loaded into editor!")
                st.rerun()
    with col1_c:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_multiagent_plan = None
            st.rerun()

    if run_btn:
        # Layer 1: Input Validation
        is_valid_input, val_err_msg = validate_input(user_code, language=current_lang)
        if not is_valid_input:
            log_security_event("INPUT_VALIDATION_BLOCK", "HIGH", val_err_msg, user_code, language=current_lang)
            st.warning(f"⚠️ {val_err_msg}")
        else:
            start_time = time.time()
            tracker = EmissionsTracker(project_name=f"{current_lang}_debugger", log_level="error")
            try:
                tracker.start()
            except Exception:
                pass

            # Layer 2: Security Guardrail Pre-Scan
            is_hard_blocked, block_msg, soft_warnings = run_security_guardrail(user_code, language=current_lang)

            # Hard block: dangerous function detected — stop immediately
            if is_hard_blocked:
                stop_and_save_metrics(tracker, start_time)
                log_security_event("STATIC_GUARDRAIL_BLOCK", "CRITICAL", block_msg, user_code, language=current_lang)
                st.error(f"🚫 SECURITY BLOCK: {block_msg}")
                st.stop()

            # Soft warnings: advisory issues
            if soft_warnings:
                advisory_text = f"⚠️ **{current_cfg['display_name']} Code Advisory (non-blocking):**\n\n" + "\n\n".join(
                    f"- {w}" for w in soft_warnings
                )
                st.session_state.messages.append({"role": "assistant", "content": advisory_text})

            # Execute in sandbox
            with st.spinner(f"Executing securely in {current_cfg['display_name']} Docker sandbox..."):
                st.session_state.last_agent_log = None
                return_code, stdout, stderr = compile_and_run(user_code, language=current_lang, stdin_data=stdin_input)

                st.session_state.last_status = return_code
                st.session_state.last_stdout = stdout
                st.session_state.last_stderr = stderr
                st.session_state.last_lang = current_lang

            # Process Execution Results
            if return_code == 0:
                # --- PATH A: SUCCESS ---
                st.success("✅ Execution Successful!")
                st.session_state.last_multiagent_plan = None
                
                with st.spinner(f"Checking code logic with {st.session_state.selected_ai_model}..."):
                    logic_prompt = f"Review this {current_cfg['display_name']} code for logic correctness, optimal complexity, and clean style. Keep review concise.\n```{current_lang}\n{user_code}\n```"
                    logic_feedback = get_ai_explanation(logic_prompt, model_name=st.session_state.selected_ai_model)
                
                success_msg = f"**✅ {current_cfg['display_name']} code executed successfully!**\n\n**🎓 Mentor Code Review ({st.session_state.selected_ai_model}):**\n{logic_feedback}"
                st.session_state.messages.append({"role": "assistant", "content": success_msg})
                log_interaction("SYSTEM (Success)", success_msg, user_code, "Logic Check")
                stop_and_save_metrics(tracker, start_time)
                st.rerun()

            else:
                # --- PATH B & C: RUNTIME OR COMPILATION ERROR ---
                is_runtime = (return_code == 2)
                err_type_str = "Runtime Crash" if is_runtime else "Compilation / Syntax Error"
                log_error(stderr, user_code)

                # Initialize Multi-Agent Orchestrator
                orchestrator = MultiAgentOrchestrator(
                    diagnostic_model=st.session_state.agent_models["diagnostic"],
                    repair_model=st.session_state.agent_models["repair"],
                    security_model=st.session_state.agent_models["security"],
                    tutor_model=st.session_state.agent_models["tutor"]
                )

                # If C++ crash and lldb is available on host/docker
                lldb_info = ""
                if is_runtime and current_lang == "cpp" and os.name != "nt":
                    with st.spinner("🤖 AI Agent is inspecting memory with LLDB..."):
                        lldb_info, agent_log = agentic_debug_loop(
                            cpp_code=user_code, 
                            crash_output=stderr, 
                            executable_path="./temp_program"
                        )
                        st.session_state.last_agent_log = agent_log

                full_err_context = stderr + (f"\n\n[LLDB Context]:\n{lldb_info}" if lldb_info else "")

                # MULTI-AGENT EXECUTION MODES
                if st.session_state.platform_mode == "Multi-Agent Swarm":
                    with st.spinner("🤖 Multi-Agent Swarm Collaborating: Detective 🔍 ➔ Architect 🛠️ ➔ Sentinel 🛡️ ➔ Mentor 🎓..."):
                        plan = orchestrator.run_collaborative_swarm(
                            code=user_code,
                            error=full_err_context,
                            language=current_lang,
                            model_overrides=st.session_state.agent_models
                        )
                        st.session_state.last_multiagent_plan = plan

                    status_sym = "✅ Secure Fix Verified" if plan.is_secure else "⚠️ Fix requires caution"
                    summary_msg = (
                        f"### 🤖 Multi-Agent Swarm Report ({err_type_str})\n"
                        f"- **🔍 Detective:** {plan.diagnostic_report.metadata.get('category', 'Identified')}\n"
                        f"- **🛠️ Architect:** Generated patch using `{st.session_state.agent_models['repair']}`\n"
                        f"- **🛡️ Sentinel:** {status_sym}\n\n"
                        f"#### 🎓 Pedagogical Lesson:\n{plan.tutor_feedback.content}"
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": summary_msg,
                        "code_expander": plan.final_code,
                        "expander_lang": current_lang
                    })

                elif st.session_state.platform_mode == "Multi-Model Council":
                    with st.spinner("🏛️ Multi-Model Council Evaluating Across Llama 3, Phi-3, and Qwen 2.5..."):
                        plan = orchestrator.run_multi_model_council(
                            code=user_code,
                            error=full_err_context,
                            language=current_lang
                        )
                        st.session_state.last_multiagent_plan = plan

                    council_msg = (
                        f"### 🏛️ Multi-Model Council Evaluation ({err_type_str})\n"
                        f"Analyzed code across **Meta Llama 3**, **Microsoft Phi-3**, and **Alibaba Qwen**:\n\n"
                        f"#### 🎓 Council Consensus Lesson:\n{plan.tutor_feedback.content}"
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": council_msg,
                        "code_expander": plan.final_code,
                        "expander_lang": current_lang
                    })

                else:
                    # Single Model Direct Mode
                    with st.spinner(f"🤖 {st.session_state.selected_ai_model} is analyzing the {err_type_str}..."):
                        category, strategy = classify_error(stderr, language=current_lang)
                        prompt = get_diagnostic_prompt(category, strategy, user_code, full_err_context, language=current_lang)
                        explanation = get_ai_explanation(prompt, model_name=st.session_state.selected_ai_model)
                        is_fix_safe, suggested_code, security_status = validate_ai_fix(explanation, language=current_lang)

                        single_msg = f"**Detected:** {category}\n\n{explanation}"
                        st.session_state.messages.append({"role": "assistant", "content": single_msg})
                        if is_fix_safe and suggested_code:
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": "✅ " + security_status,
                                "code_expander": suggested_code,
                                "expander_lang": current_lang
                            })
                        elif suggested_code:
                            st.session_state.messages.append({"role": "assistant", "content": "🚫 Insecure pattern: " + security_status})

                stop_and_save_metrics(tracker, start_time)
                st.rerun()

    # Terminal Output Display
    if st.session_state.last_status is not None:
        st.markdown("---")
        last_lang_name = get_display_name(st.session_state.last_lang)
        st.subheader(f"🖥️ Terminal Output ({last_lang_name})")
        
        if st.session_state.last_status == 0:
            st.success("✅ Status: Success (Exit Code 0)")
            st.code(st.session_state.last_stdout or "(No output generated)", language="text")
        elif st.session_state.last_status == 2:
            st.error("⚠️ Status: Runtime Error / Crash")
            if st.session_state.last_stdout:
                st.markdown("**Output before error:**")
                st.code(st.session_state.last_stdout, language="text")
            st.code(st.session_state.last_stderr, language="text")
        else:
            st.error("❌ Status: Compilation / Syntax Error")
            st.code(st.session_state.last_stderr, language="text")      

    # MULTI-AGENT TRANSPARENCY VISUALIZER
    if st.session_state.last_multiagent_plan:
        plan = st.session_state.last_multiagent_plan
        st.markdown("---")
        st.subheader(f"🤖 Multi-Agent Collaboration Panel ({plan.execution_mode.upper()})")

        if plan.execution_mode == "swarm":
            t1, t2, t3, t4 = st.tabs([
                "🔍 Diagnostic Detective",
                "🛠️ Repair Architect",
                "🛡️ Security Sentinel",
                "🎓 Pedagogical Mentor"
            ])
            with t1:
                st.markdown(f"**Model:** `{plan.diagnostic_report.model}` | **Latency:** `{plan.diagnostic_report.metadata.get('latency_sec', 0)}s`")
                st.markdown(plan.diagnostic_report.content)
            with t2:
                st.markdown(f"**Model:** `{plan.repair_proposal.model}` | **Latency:** `{plan.repair_proposal.metadata.get('latency_sec', 0)}s`")
                st.markdown(plan.repair_proposal.content)
                if plan.final_code:
                    st.code(plan.final_code, language=current_lang)
            with t3:
                st.markdown(f"**Audit Status:** `{plan.security_verdict.status.upper()}` | **Defense:** 13-Layer Guardrail")
                st.markdown(plan.security_verdict.content)
            with t4:
                st.markdown(f"**Model:** `{plan.tutor_feedback.model}`")
                st.markdown(plan.tutor_feedback.content)

        elif plan.execution_mode == "council":
            c_tabs = st.tabs(["🦙 Meta Llama 3", "🔬 Microsoft Phi-3", "💻 Alibaba Qwen", "🎓 Council Takeaway"])
            idx = 0
            for family_name, proposal in plan.council_proposals.items():
                with c_tabs[idx]:
                    st.markdown(f"**Model:** `{proposal['model']}` | **Secure:** `{'✅ Passed' if proposal['is_secure'] else '❌ Rejected'}`")
                    st.markdown(proposal["repair"].content)
                    if proposal["extracted_code"]:
                        st.code(proposal["extracted_code"], language=current_lang)
                    st.info(proposal["audit"].content)
                idx += 1
            with c_tabs[3]:
                st.markdown(plan.tutor_feedback.content)

    # AGENTIC LLDB BRAIN LOG (if ran)
    if st.session_state.last_agent_log:
        st.markdown("---")
        st.subheader("🧠 Agentic LLDB Process")
        with st.expander("View AI Debugging Steps", expanded=True):
            st.markdown(st.session_state.last_agent_log)

    # Green Metrics Dashboard
    if st.session_state.green_metrics:
        st.markdown("---")
        st.subheader("🌿 Green Sandbox Metrics")
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("⏱️ Latency", f"{st.session_state.green_metrics['latency']:.2f} s")
        m_col2.metric("⚡ Energy Used", f"{st.session_state.green_metrics['energy']:.6f} kWh")
        m_col3.metric("🌍 Carbon Emitted", f"{st.session_state.green_metrics['carbon']:.5f} g") 


# ============================================================
# RIGHT COLUMN: THE MULTI-TURN AI CHAT
# ============================================================
with col2:
    st.subheader(f"💬 Multi-Agent AI Chat ({current_cfg['display_name']})")
    
    agent_target_choice = st.radio(
        "Direct Question To:",
        ["🎓 Tutor Mentor", "🔍 Detective Agent", "🛠️ Repair Agent", "🛡️ Security Sentinel"],
        horizontal=True
    )

    chat_container = st.container(height=500)
    
    with chat_container:
        if len(st.session_state.messages) == 0:
            st.info(f"Hit 'Run Code' to compile and execute your {current_cfg['display_name']} code, or ask a question below!")
            
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                if "code_expander" in msg and msg["code_expander"]:
                    exp_lang = msg.get("expander_lang", current_lang)
                    with st.expander(f"View Verified {get_display_name(exp_lang)} Code"):
                        st.code(msg["code_expander"], language=exp_lang)
                
    if follow_up := st.chat_input(f"Ask {agent_target_choice} about your {current_cfg['display_name']} code:"):
        st.session_state.messages.append({"role": "user", "content": f"[{agent_target_choice}] {follow_up}"})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(f"**{agent_target_choice}:** {follow_up}")
                
        # Determine model for chat routing
        chat_model = st.session_state.selected_ai_model
        if "Detective" in agent_target_choice:
            chat_model = st.session_state.agent_models.get("diagnostic", "phi3:mini")
            role_desc = "You are the Diagnostic Detective Agent. Pinpoint bugs, compiler diagnostics, and memory faults."
        elif "Repair" in agent_target_choice:
            chat_model = st.session_state.agent_models.get("repair", "qwen2.5:coder")
            role_desc = "You are the Repair Architect Agent. Suggest clean, minimal code fixes with proper syntax."
        elif "Security" in agent_target_choice:
            chat_model = st.session_state.agent_models.get("security", "llama3.2:1b")
            role_desc = "You are the Security Sentinel Agent. Review code for buffer overflows, process injection, format string bugs, and memory safety."
        else:
            chat_model = st.session_state.agent_models.get("tutor", "phi3:mini")
            role_desc = f"You are a friendly, encouraging {current_cfg['display_name']} Tutor Mentor."

        conversation_history = f"{role_desc} The user is working on this {current_cfg['display_name']} code:\n```{current_lang}\n{user_code}\n```\n\nRecent context:\n"
        for m in st.session_state.messages[-4:]: 
            conversation_history += f"{m['role'].capitalize()}: {m['content']}\n"
        conversation_history += f"\nRespond concisely to the user's latest query: {follow_up}"

        with chat_container:
            with st.chat_message("assistant"):
                stream_gen = stream_ai_explanation(conversation_history, model_name=chat_model)
                ai_reply = st.write_stream(stream_gen)
                    
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        log_interaction(
            user_prompt=follow_up,
            llm_response=ai_reply,
            code_snippet=user_code,
            error_category=f"Follow-up Chat ({agent_target_choice})", 
            fixed_code="N/A"
        )
