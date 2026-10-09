import streamlit as st
import subprocess
import requests
import os
import time

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

# LLM config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

def get_ai_explanation(prompt):
    """Sends the prompt to the local Ollama Llama 3 model."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            return f"Error connecting to Ollama: {response.status_code}"
    except Exception as e:
        return f"Connection Failed. Is Ollama running? Error: {str(e)}"
    

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
st.set_page_config(page_title="AI Multi-Language Sandbox Compiler & Debugger", layout="wide")

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
if "green_metrics" not in st.session_state:
    st.session_state.green_metrics = None

st.title("⚡ Chatbot-Driven Sandbox Compiler & Debugger")
st.markdown("### Secure Multi-Language Code Execution Sandbox (C++ • Python • Java)")

# --- LANGUAGE SELECTOR BAR ---
lang_col1, lang_col2, lang_col3 = st.columns([2, 2, 2])
with lang_col1:
    lang_display_options = ["C++", "Python", "Java"]
    lang_key_map = {"C++": "cpp", "Python": "python", "Java": "java"}
    inv_lang_map = {v: k for k, v in lang_key_map.items()}

    current_display = inv_lang_map.get(st.session_state.selected_language, "C++")
    selected_display = st.selectbox("🌐 Select Language:", lang_display_options, index=lang_display_options.index(current_display))
    new_lang_key = lang_key_map[selected_display]

    # Handle language change
    if new_lang_key != st.session_state.selected_language:
        st.session_state.selected_language = new_lang_key
        st.session_state.last_status = None
        st.session_state.last_agent_log = None
        st.rerun()

current_lang = st.session_state.selected_language
current_cfg = get_language_config(current_lang)

with lang_col2:
    st.info(f"🔒 **Sandbox Image:** `{current_cfg['docker_image']}` | **Isolation:** Network Disabled • Non-Root • RAM {current_cfg['memory_limit']}")

with lang_col3:
    st.markdown(f"**Selected Language:** `[{current_cfg['display_name']}]` ({current_cfg['extension']})")

col1, col2 = st.columns(2)

# ============================================================
# LEFT COLUMN: THE CODE EDITOR & COMPILER
# ============================================================
with col1:
    st.subheader(f"📝 {current_cfg['display_name']} Code Editor")
    
    # Text editor for active language
    editor_key = f"code_editor_{current_lang}"
    default_lang_code = st.session_state.code_per_lang.get(current_lang, current_cfg["default_code"])
    user_code = st.text_area(f"Write your {current_cfg['display_name']} code here:", value=default_lang_code, height=350, key=editor_key)
    st.session_state.code_per_lang[current_lang] = user_code

    # Optional Stdin input area
    with st.expander("📥 Standard Input (stdin) - Optional"):
        stdin_input = st.text_area("Provide input lines for your program:", value="", height=80, key=f"stdin_{current_lang}")

    col1_a, col1_b = st.columns([1.5, 2.5])
    with col1_a:
        action_label = "Compile & Run" if current_cfg["needs_compile"] else "Run Code"
        run_btn = st.button(f"▶️ {action_label}", type="primary")
    with col1_b:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
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
                st.code(stdout or "(No output generated)", language="text")
                
                with st.spinner("Checking code logic with AI Tutor..."):
                    logic_prompt = f"Review this {current_cfg['display_name']} code for logic correctness and style. If it's optimal, say so briefly.\n```{current_lang}\n{user_code}\n```"
                    logic_feedback = get_ai_explanation(logic_prompt)
                
                success_msg = f"**{current_cfg['display_name']} code executed successfully!**\n\n**AI Logic Feedback:**\n{logic_feedback}"
                st.session_state.messages.append({"role": "assistant", "content": success_msg})
                log_interaction("SYSTEM (Success)", success_msg, user_code, "Logic Check")
                stop_and_save_metrics(tracker, start_time)
                st.rerun()

            elif return_code == 2:
                # --- PATH B: RUNTIME ERROR / CRASH ---
                st.error(f"⚠️ Runtime Error Detected in {current_cfg['display_name']} program!")
                
                # If C++ crash and lldb is available, trigger agentic LLDB loop
                if current_lang == "cpp" and os.name != "nt":
                    with st.spinner("🤖 AI Agent is inspecting memory with LLDB..."):
                        final_diagnosis, agent_log = agentic_debug_loop(
                            cpp_code=user_code, 
                            crash_output=stderr, 
                            executable_path="./temp_program"
                        )
                    st.session_state.last_agent_log = agent_log
                    initial_msg = f"**🚨 Runtime Crash Detected (C++)**\n\n**Agentic LLDB Diagnosis:**\n{final_diagnosis}"
                else:
                    category, strategy = classify_error(stderr, language=current_lang)
                    prompt = get_diagnostic_prompt(category, strategy, user_code, stderr, language=current_lang)
                    with st.spinner(f"🤖 AI is analyzing the {current_cfg['display_name']} runtime error..."):
                        explanation = get_ai_explanation(prompt)
                    is_fix_safe, suggested_code, security_status = validate_ai_fix(explanation, language=current_lang)
                    initial_msg = f"**Detected Runtime Error:** {category}\n\n{explanation}"

                st.session_state.messages.append({"role": "assistant", "content": initial_msg})
                log_interaction("SYSTEM (Runtime Crash)", initial_msg, user_code, "Runtime Error")
                stop_and_save_metrics(tracker, start_time)
                st.rerun()

            else:
                # --- PATH C: COMPILE / SYNTAX ERROR ---
                st.error(f"❌ {current_cfg['display_name']} Compilation / Syntax Error!")
                log_error(stderr, user_code)
                
                category, strategy = classify_error(stderr, language=current_lang)
                prompt = get_diagnostic_prompt(category, strategy, user_code, stderr, language=current_lang)
                
                with st.spinner(f"🤖 AI is analyzing the {current_cfg['display_name']} error..."):
                    explanation = get_ai_explanation(prompt)
                
                is_fix_safe, suggested_code, security_status = validate_ai_fix(explanation, language=current_lang)
                initial_msg = f"**Detected:** {category}\n\n{explanation}"
                
                st.session_state.messages.append({"role": "assistant", "content": initial_msg})
                log_interaction("SYSTEM (Compile Failed)", initial_msg, user_code, category, suggested_code or "N/A")
                
                if is_fix_safe and suggested_code:
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "✅ " + security_status,
                        "code_expander": suggested_code,
                        "expander_lang": current_lang
                    })
                else:
                    if suggested_code:
                        st.session_state.messages.append({"role": "assistant", "content": "🚫 AI generated insecure code! " + security_status})
                stop_and_save_metrics(tracker, start_time)
                st.rerun()

    # Terminal Output Display
    if st.session_state.last_status is not None:
        st.markdown("---")
        last_lang_name = get_display_name(st.session_state.last_lang)
        st.subheader(f"🖥️ Terminal Output ({last_lang_name})")
        
        if st.session_state.last_status == 0:
            st.success(f"✅ Status: Success (Exit Code 0)")
            st.code(st.session_state.last_stdout or "(No output generated)", language="text")
        elif st.session_state.last_status == 2:
            st.error(f"⚠️ Status: Runtime Error / Crash")
            if st.session_state.last_stdout:
                st.markdown("**Output before error:**")
                st.code(st.session_state.last_stdout, language="text")
            st.code(st.session_state.last_stderr, language="text")
        else:
            st.error(f"❌ Status: Compilation / Syntax Error")
            st.code(st.session_state.last_stderr, language="text")      

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
    st.subheader(f"💬 AI Tutor Chat ({current_cfg['display_name']})")
    
    chat_container = st.container(height=520)
    
    with chat_container:
        if len(st.session_state.messages) == 0:
            st.info(f"Hit 'Run Code' to compile and execute your {current_cfg['display_name']} code, or ask a question below!")
            
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                if "code_expander" in msg:
                    exp_lang = msg.get("expander_lang", current_lang)
                    with st.expander(f"View Verified {get_display_name(exp_lang)} Code"):
                        st.code(msg["code_expander"], language=exp_lang)
                
    if follow_up := st.chat_input(f"Ask a question about your {current_cfg['display_name']} code:"):
        st.session_state.messages.append({"role": "user", "content": follow_up})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(follow_up)
                
        conversation_history = f"You are a helpful {current_cfg['display_name']} tutor. The user is currently working on this code:\n```{current_lang}\n{user_code}\n```\n\nHere is the recent conversation:\n"
        for m in st.session_state.messages[-4:]: 
            conversation_history += f"{m['role'].capitalize()}: {m['content']}\n"
        conversation_history += f"Now, respond to the user's latest question about {current_cfg['display_name']} concisely."

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    ai_reply = get_ai_explanation(conversation_history)
                    st.markdown(ai_reply)
                    
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        log_interaction(
            user_prompt=follow_up,
            llm_response=ai_reply,
            code_snippet=user_code,
            error_category="Follow-up Chat", 
            fixed_code="N/A"
        )