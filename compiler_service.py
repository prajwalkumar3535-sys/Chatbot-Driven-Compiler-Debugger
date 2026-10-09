"""
compiler_service.py - Unified Multi-Language Compilation & Execution Service
Supports C++, Python, and Java.
Maintains full backward compatibility with the existing C++ reference implementation.
"""

import subprocess
import os
import shutil

from language_config import get_language_config, validate_language, ALLOWED_LANGUAGES
from language_executor import execute_in_sandbox, is_docker_engine_ready
from docker_executor import compile_in_docker, run_in_docker
from output_controller import enforce_output_limits, sanitize_terminal_output
from timeout_controller import run_command_with_timeout, ExecutionTimeoutException

SANDBOX_IMAGE = "cpp-sandbox"
SANDBOX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_env"))


def ensure_sandbox_env():
    """Ensures isolated sandbox folder exists."""
    os.makedirs(SANDBOX_DIR, exist_ok=True)


def is_docker_available() -> bool:
    """Checks if Docker daemon is running and image is available."""
    return is_docker_engine_ready()


def _compile_and_run_docker(sandbox_dir: str = SANDBOX_DIR, language: str = "cpp", stdin_data: str = ""):
    """
    Executes compilation and run inside isolated Docker container via language_executor.
    """
    # For C++ with default parameters, we can use the universal executor
    result = execute_in_sandbox(language=language, source_code="", stdin_data=stdin_data)
    rc = result["status_code"]
    if rc == 0:
        return 0, result["stdout"], ""
    elif rc == 1:
        return 1, result["stdout"], result["stderr"]
    elif rc == 2:
        return 2, result["stdout"], result["stderr"]
    else:
        return -1, result["stdout"], result["stderr"]


def _compile_and_run_host(code: str, language: str = "cpp", stdin_data: str = ""):
    """Fallback if Docker is not available on the host machine."""
    lang = (language or "cpp").lower().strip()

    if lang == "python":
        py_file = os.path.join(SANDBOX_DIR, "solution.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            proc = subprocess.run(
                ["python", py_file],
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=5,
            )
            out = proc.stdout
            err = proc.stderr
            if proc.returncode != 0:
                return 2, out, err
            return 0, (out + ("\n" + err if err else "")).strip(), ""
        except subprocess.TimeoutExpired:
            return -1, "", "[ERROR] Time Limit Exceeded (5s)! Possible infinite loop."
        except Exception as e:
            return -1, "", f"[ERROR] System Error: {e}"

    elif lang == "java":
        java_file = os.path.join(SANDBOX_DIR, "Main.java")
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            c_proc = subprocess.run(
                ["javac", "-d", SANDBOX_DIR, java_file],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if c_proc.returncode != 0:
                return 1, "", c_proc.stderr

            r_proc = subprocess.run(
                ["java", "-cp", SANDBOX_DIR, "Main"],
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=5,
            )
            out = r_proc.stdout
            err = r_proc.stderr
            if r_proc.returncode != 0:
                return 2, out, err
            return 0, (out + ("\n" + err if err else "")).strip(), ""
        except subprocess.TimeoutExpired:
            return -1, "", "[ERROR] Time Limit Exceeded (5s)! Possible infinite loop."
        except Exception as e:
            return -1, "", f"[ERROR] System Error: {e}"

    else:
        # C++ fallback
        if os.name == "nt":
            try:
                import ctypes
                SEM_FAILCRITICALERRORS = 0x0001
                SEM_NOGPFAULTERRORBOX = 0x0002
                SEM_NOOPENFILEERRORBOX = 0x8000
                ctypes.windll.kernel32.SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX)
            except Exception:
                pass

        source_file = os.path.join(SANDBOX_DIR, "temp_source.cpp")
        executable = os.path.join(SANDBOX_DIR, "temp_program.exe" if os.name == "nt" else "temp_program")

        with open(source_file, "w", encoding="utf-8") as f:
            f.write(code)

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
                input=stdin_data if stdin_data else None,
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


def compile_and_run(code: str, language: str = "cpp", stdin_data: str = "") -> tuple[int, str, str]:
    """
    Universal multi-language compile and run function.
    
    Arguments:
        code: Source code string
        language: 'cpp' | 'python' | 'java' (defaults to 'cpp' for backward compatibility)
        stdin_data: Optional input to pass to the running program
        
    Returns: (status_code, stdout, stderr)
      0 = Success
      1 = Compile Error
      2 = Runtime Error (Segfault/Crash/Exception)
     -1 = Timeout/System Error
    """
    ensure_sandbox_env()
    lang = (language or "cpp").lower().strip()

    if is_docker_available():
        res = execute_in_sandbox(language=lang, source_code=code, stdin_data=stdin_data)
        rc = res["status_code"]
        if rc == 0:
            return 0, res["stdout"], ""
        elif rc == 1:
            return 1, res["stdout"], res["stderr"]
        elif rc == 2:
            return 2, res["stdout"], res["stderr"]
        else:
            return -1, res["stdout"], res["stderr"]
    else:
        return _compile_and_run_host(code=code, language=lang, stdin_data=stdin_data)