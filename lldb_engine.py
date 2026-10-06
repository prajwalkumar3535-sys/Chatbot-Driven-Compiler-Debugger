import subprocess
import requests
import json
import os
import shutil

# LLM config (Must match your app.py)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

SANDBOX_IMAGE = "cpp-sandbox"
SANDBOX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_env"))

def is_docker_available():
    """Checks if Docker daemon is running."""
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False

def execute_lldb_command(executable_path, command):
    """
    Runs a specific LLDB command on the compiled binary in batch mode.
    Executes securely within the Docker sandbox when available.
    """
    if is_docker_available():
        try:
            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--cap-add=SYS_PTRACE",
                "--security-opt", "seccomp=unconfined",
                "-v", f"{SANDBOX_DIR}:/sandbox",
                SANDBOX_IMAGE,
                "lldb", "-b",
                "-o", "settings set target.disable-aslr false",
                "-o", "run",
                "-o", command,
                "-o", "quit",
                "/sandbox/prog"
            ]
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=12
            )
            output = result.stdout or result.stderr
            # Filter out any container Python wrapper warnings
            cleaned_lines = [
                line for line in output.splitlines() 
                if not line.startswith("Traceback") and 
                   not line.startswith("  File") and 
                   not line.startswith("ModuleNotFoundError")
            ]
            return "\n".join(cleaned_lines).strip()
        except subprocess.TimeoutExpired:
            return "LLDB Timeout: The command took too long to execute in sandbox."
        except Exception as e:
            return f"LLDB Sandbox Error: {str(e)}"
    else:
        try:
            lldb_path = os.environ.get("LLDB_PATH") or shutil.which("lldb")
            if not lldb_path:
                return "LLDB not found. Add lldb to PATH, start Docker for containerized debugging, or set LLDB_PATH."

            result = subprocess.run(
                [lldb_path, "-b", "-o", "run", "-o", command, executable_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "LLDB Timeout: The command took too long to execute."
        except Exception as e:
            return f"LLDB System Error: {str(e)}"

def agentic_debug_loop(cpp_code, crash_output, executable_path="./temp_program"):
    """
    The ReAct (Reason & Act) Loop.
    Allows Llama 3 to autonomously run LLDB commands to inspect memory.
    """
    
    print("\n[SYSTEM] 🤖 Initiating Agentic LLDB Loop inside Sandbox...")
    
    # 1. The Strict Agentic System Prompt
    agent_prompt = f"""You are an Autonomous C++ Debugger running inside a secure sandbox.
A C++ program just crashed with a Runtime Error (e.g., Segmentation Fault).

--- BUGGY CODE ---
{cpp_code}

--- CRASH OUTPUT ---
{crash_output}

You have access to the LLDB Debugger. 
You must choose ONE of the following actions:
ACTION 1: Run an LLDB command to inspect memory (e.g., 'bt' for backtrace, or 'frame variable' to see local variables).
ACTION 2: Explain the error and provide the fix.

You MUST respond in strict JSON format:
{{
    "thought": "Your reasoning about what to do next",
    "action": "lldb_command" OR "final_fix",
    "command": "the exact lldb command to run (leave empty if final_fix)",
    "explanation": "Your final explanation to the user. You MUST include the fully corrected C++ code inside a markdown block. (leave empty if lldb_command)"
}}"""

    max_turns = 2
    current_context = agent_prompt
    ui_debug_log = "" 

    for turn in range(max_turns):
        print(f"[SYSTEM] Turn {turn + 1}: Asking Llama 3 for its next move...")
        
        payload = {"model": MODEL_NAME, "prompt": current_context, "stream": False, "format": "json"}
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=30).json()['response']
        except Exception as e:
            return f"Failed to connect to LLM for debugging: {str(e)}", ui_debug_log
        
        try:
            ai_decision = json.loads(response)
            thought = ai_decision.get('thought')
            action = ai_decision.get('action')
            
            print(f"   [LLM THOUGHT]: {thought}")
            ui_debug_log += f"**Turn {turn + 1} - 🧠 Thought:** {thought}\n\n"
            
            if action == "lldb_command":
                cmd = ai_decision.get("command")
                print(f"   [LLM ACTION]: Running LLDB command -> `{cmd}`")
                
                ui_debug_log += f"**🛠️ Action:** Ran LLDB command `{cmd}`\n\n"
                
                lldb_result = execute_lldb_command(executable_path, cmd)
                
                ui_debug_log += f"**💻 LLDB Response:**\n```text\n{lldb_result}\n```\n\n---\n\n"
                
                current_context += f"\n\n--- LLDB RESULT FOR '{cmd}' ---\n{lldb_result}\n\nNow, provide the 'final_fix' JSON based on this new memory data."
            
            elif action == "final_fix":
                print("   [LLM ACTION]: Delivering final fix.")
                ui_debug_log += "**✅ Action:** Diagnosis Complete. Delivering final fix."
                return ai_decision.get("explanation"), ui_debug_log 
                
        except json.JSONDecodeError:
            return "Critical Error: The AI failed to output valid JSON routing.", ui_debug_log

    return "Agentic Loop Halted: AI exceeded maximum allowed debugging turns.", ui_debug_log
