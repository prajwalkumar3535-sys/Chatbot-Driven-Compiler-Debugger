import subprocess
import os
import shutil

SANDBOX_IMAGE = "cpp-sandbox"
SANDBOX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_env"))

def ensure_sandbox_env():
    """Ensures isolated sandbox folder exists."""
    os.makedirs(SANDBOX_DIR, exist_ok=True)

def is_docker_available():
    """Checks if Docker daemon is running and image is available."""
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False

def _compile_and_run_docker(sandbox_dir):
    """
    Executes compilation and run inside isolated Docker container with strict constraints:
    - No network access (--network none)
    - 256MB RAM limit (--memory 256m)
    - 1 CPU limit (--cpus 1.0)
    - Max 32 PIDs to prevent fork bombs (--pids-limit 32)
    - Drops Linux kernel capabilities (--cap-drop ALL)
    """
    # 1. COMPILE IN DOCKER
    compile_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1.0",
        "-v", f"{sandbox_dir}:/sandbox",
        SANDBOX_IMAGE,
        "sh", "-c", "g++ -g /sandbox/solution.cpp -o /sandbox/prog"
    ]

    try:
        compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=12)
        if compile_proc.returncode != 0:
            return 1, "", compile_proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "[ERROR] Compilation Time Limit Exceeded!"
    except Exception as e:
        return -1, "", f"[ERROR] Sandbox Compilation Error: {str(e)}"

    # 2. RUN BINARY IN ISOLATED DOCKER SANDBOX
    run_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "256m",
        "--cpus", "1.0",
        "--pids-limit", "32",
        "--cap-drop", "ALL",
        "-v", f"{sandbox_dir}:/sandbox",
        SANDBOX_IMAGE,
        "/sandbox/prog"
    ]

    try:
        run_proc = subprocess.run(run_cmd, capture_output=True, text=True, timeout=5)
        
        # 3. CATCH RUNTIME CRASHES (Linux signal exit codes)
        linux_crash_signals = {
            139: "Segmentation Fault (SIGSEGV) - Invalid memory access / null pointer dereference",
            134: "Process Aborted (SIGABRT) - Assertion failed / Double free / Memory corruption",
            136: "Floating Point Exception (SIGFPE) - Division by zero",
            137: "Out of Memory (SIGKILL) - Memory limit exceeded (256MB cap)",
            138: "Bus Error (SIGBUS) - Misaligned memory access",
            143: "Process Terminated (SIGTERM)",
        }

        if run_proc.returncode in linux_crash_signals:
            crash_reason = run_proc.stderr if run_proc.stderr else linux_crash_signals[run_proc.returncode]
            return 2, run_proc.stdout, f"Process crashed (Exit Code {run_proc.returncode}): {crash_reason}"
        elif run_proc.returncode != 0 and run_proc.returncode > 128:
            return 2, run_proc.stdout, f"Process crashed with signal exit code {run_proc.returncode}.\n{run_proc.stderr}"
        elif run_proc.returncode != 0:
            # Non-zero exit (e.g. user returned 1 or custom exit code)
            full_out = run_proc.stdout
            if run_proc.stderr:
                full_out += ("\n" if full_out else "") + run_proc.stderr
            return 0, full_out.strip(), ""

        # 4. GRACEFUL SUCCESS
        full_out = run_proc.stdout
        if run_proc.stderr:
            full_out += ("\n" if full_out else "") + run_proc.stderr
        return 0, full_out.strip(), ""

    except subprocess.TimeoutExpired:
        return -1, "", "[ERROR] Time Limit Exceeded (5s)! Possible infinite loop or blocking call."
    except Exception as e:
        return -1, "", f"[ERROR] Sandbox Runtime Error: {str(e)}"

def _compile_and_run_host(cpp_code):
    """Fallback if Docker is not available."""
    source_file = os.path.join(SANDBOX_DIR, "temp_source.cpp")
    executable = os.path.join(SANDBOX_DIR, "temp_program.exe" if os.name == "nt" else "temp_program")

    with open(source_file, "w", encoding="utf-8") as f:
        f.write(cpp_code)

    try:
        compile_process = subprocess.run(
            ["g++", "-g", source_file, "-o", executable],
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if compile_process.returncode != 0:
            return 1, "", compile_process.stderr

        run_process = subprocess.run(
            [executable], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        windows_crash_codes = {0xC0000005, 0xC00000FD, 0xC000001D, 0xC0000094}
        if run_process.returncode < 0 or run_process.returncode in windows_crash_codes:
            crash_reason = run_process.stderr if run_process.stderr else f"Process crashed with exit code {run_process.returncode} (Likely Segmentation Fault)"
            return 2, run_process.stdout, crash_reason

        full_output = run_process.stdout
        if run_process.stderr:
            full_output += "\n" + run_process.stderr
        return 0, full_output.strip(), ""
    except subprocess.TimeoutExpired:
        return -1, "", "[ERROR] Time Limit Exceeded! Possible infinite loop."
    except Exception as e:
        return -1, "", f"[ERROR] System Error: {str(e)}"

def compile_and_run(cpp_code):
    """
    Compiles with '-g' for LLDB support and runs the code.
    Returns: (status_code, stdout, stderr)
      0 = Success
      1 = Compile Error
      2 = Runtime Error (Segfault/Crash)
     -1 = Timeout/System Error
    """
    ensure_sandbox_env()
    source_file = os.path.join(SANDBOX_DIR, "solution.cpp")
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(cpp_code)

    if is_docker_available():
        return _compile_and_run_docker(SANDBOX_DIR)
    else:
        return _compile_and_run_host(cpp_code)