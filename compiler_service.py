import subprocess
import os
import shutil

SANDBOX_IMAGE = "cpp-sandbox"
SANDBOX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_env"))

def ensure_sandbox_env():
    """Ensures isolated sandbox folder exists."""
    os.makedirs(SANDBOX_DIR, exist_ok=True)

from docker_executor import compile_in_docker, run_in_docker, is_docker_engine_ready
from output_controller import enforce_output_limits, sanitize_terminal_output
from timeout_controller import run_command_with_timeout, ExecutionTimeoutException

def is_docker_available():
    """Checks if Docker daemon is running and image is available."""
    return is_docker_engine_ready()

def _compile_and_run_docker(sandbox_dir):
    """
    Executes compilation and run inside isolated Docker container via docker_executor.
    """
    code, stdout, stderr = compile_in_docker(sandbox_dir)
    if code != 0:
        return code, stdout, stderr
    return run_in_docker(sandbox_dir)

def _compile_and_run_host(cpp_code):
    """Fallback if Docker is not available."""
    if os.name == "nt":
        try:
            import ctypes
            # Disable Windows crash dialogs so process terminates immediately on segfault
            SEM_FAILCRITICALERRORS = 0x0001
            SEM_NOGPFAULTERRORBOX = 0x0002
            SEM_NOOPENFILEERRORBOX = 0x8000
            ctypes.windll.kernel32.SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX)
        except Exception:
            pass

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
        windows_crash_codes = {0xC0000005, 0xC00000FD, 0xC000001D, 0xC0000094, 0xC0000028}
        rc = run_process.returncode
        is_crash = (
            rc < 0 or
            (rc & 0xFFFFFFFF) in windows_crash_codes or
            (rc & 0xFFFFFFFF) >= 0x80000000 or
            (rc > 128 and os.name != "nt")
        )
        if is_crash:
            crash_reason = run_process.stderr if run_process.stderr else f"Process crashed with exit code {rc} (Likely Segmentation Fault / Access Violation)"
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