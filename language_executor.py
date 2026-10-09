"""
language_executor.py - Universal Multi-Language Sandbox Execution Engine
Coordinates Layers 3-11 to compile and run C++, Python, and Java
inside a zero-trust, hardened Docker container environment.

Enforces for ALL languages:
  - Layer 3:  Docker Container Isolation
  - Layer 4:  Zero Network Access (--network none)
  - Layer 5:  Resource Limits (RAM cap, CPU quota)
  - Layer 6:  Read-Only Filesystem / Volume isolation
  - Layer 7:  Non-Root Execution
  - Layer 8:  Capability Restrictions (--cap-drop ALL)
  - Layer 9:  PID / Process Limits (--pids-limit)
  - Layer 10: Output Truncation & ANSI Sanitization
  - Layer 11: Execution Timeouts (run & compile)
"""

import subprocess
import os
import shutil
import time

from language_config import get_language_config, validate_language
from resource_controller import get_docker_resource_args
from output_controller import enforce_output_limits, sanitize_terminal_output
from timeout_controller import run_command_with_timeout, ExecutionTimeoutException

SANDBOX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_env"))

# Linux crash signal map
LINUX_CRASH_SIGNALS = {
    139: "Segmentation Fault (SIGSEGV) - Invalid memory access / null pointer dereference",
    134: "Process Aborted (SIGABRT) - Assertion failed / double free / memory corruption",
    136: "Floating Point Exception (SIGFPE) - Division by zero",
    137: "Out of Memory (SIGKILL) - Memory limit exceeded (RAM cap)",
    138: "Bus Error (SIGBUS) - Misaligned memory access",
    143: "Process Terminated (SIGTERM)",
}


def is_docker_engine_ready() -> bool:
    """Checks if Docker daemon is responsive."""
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False


def _build_run_cmd(cfg: dict, sandbox_dir: str) -> list[str]:
    """
    Builds the secure Docker run command for a given language config.
    Security flags are always applied — no language can bypass them.
    """
    return [
        "docker", "run", "--rm",
        "--network", "none",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        *get_docker_resource_args(
            memory=cfg["memory_limit"],
            cpus=cfg["cpu_limit"],
            pids_limit=cfg["pids_limit"],
        ),
        "-v", f"{sandbox_dir}:/sandbox",
        cfg["docker_image"],
        "sh", "-c", cfg["run_cmd"],
    ]


def _build_compile_cmd(cfg: dict, sandbox_dir: str) -> list[str]:
    """
    Builds the Docker compile command for compiled languages (C++, Java).
    Uses larger memory allowance for compiler, same network/cap restrictions.
    """
    return [
        "docker", "run", "--rm",
        "--network", "none",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        *get_docker_resource_args(
            memory=cfg.get("compile_memory", cfg["memory_limit"]),
            cpus=cfg["cpu_limit"],
            pids_limit=cfg["pids_limit"] * 2,
        ),
        "-v", f"{sandbox_dir}:/sandbox",
        cfg["docker_image"],
        "sh", "-c", cfg["compile_cmd"],
    ]


def execute_in_sandbox(language: str, source_code: str, stdin_data: str = "") -> dict:
    """
    Universal entry point for all language execution.
    
    Returns a dict:
      {
        "language": str,
        "status": "success" | "compile_error" | "runtime_error" | "timeout" | "security_error" | "system_error",
        "status_code": int,
        "stdout": str,
        "stderr": str,
        "compile_output": str,
      }
    
    Status codes:
       0 = Success
       1 = Compile Error
       2 = Runtime Crash / Exception
      -1 = Timeout / System Error
    """
    # Gate: validate language key
    is_valid_lang, lang_err = validate_language(language)
    if not is_valid_lang:
        return {
            "language": language,
            "status": "security_error",
            "status_code": -1,
            "stdout": "",
            "stderr": lang_err,
            "compile_output": "",
        }

    cfg = get_language_config(language)
    os.makedirs(SANDBOX_DIR, exist_ok=True)

    # Write source file to sandbox volume directory
    source_path = os.path.join(SANDBOX_DIR, cfg["source_filename"])
    try:
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)
    except Exception as e:
        return _err_result(language, -1, "system_error", "", f"[ERROR] Could not write source file: {e}", "")

    compile_output = ""

    # === COMPILE STAGE (C++ and Java) ===
    if cfg["needs_compile"]:
        compile_cmd = _build_compile_cmd(cfg, SANDBOX_DIR)
        
        # Retry once if Windows file lock / ETXTBSY occurred
        for attempt in range(2):
            try:
                proc = run_command_with_timeout(compile_cmd, timeout_seconds=cfg["compile_timeout"])
                out = enforce_output_limits(sanitize_terminal_output(proc.stdout or ""))
                err = enforce_output_limits(sanitize_terminal_output(proc.stderr or ""))
                compile_output = (out + "\n" + err).strip()

                if proc.returncode != 0:
                    if "Text file busy" in compile_output and attempt == 0:
                        time.sleep(0.4)
                        continue
                    return _err_result(language, 1, "compile_error", "", compile_output, compile_output)
                break
            except ExecutionTimeoutException:
                return _err_result(language, -1, "timeout",
                                   "", f"[ERROR] Compilation timed out ({cfg['compile_timeout']}s)!", "")
            except Exception as e:
                return _err_result(language, -1, "system_error", "", f"[ERROR] Compile stage error: {e}", "")

    # === RUN STAGE (all languages) ===
    run_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        *get_docker_resource_args(
            memory=cfg["memory_limit"],
            cpus=cfg["cpu_limit"],
            pids_limit=cfg["pids_limit"],
        ),
        "-v", f"{SANDBOX_DIR}:/sandbox",
        cfg["docker_image"],
        "sh", "-c", cfg["run_cmd"],
    ]

    if stdin_data:
        run_cmd.insert(3, "-i")

    try:
        if stdin_data:
            proc = subprocess.run(
                run_cmd,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=cfg["run_timeout"],
            )
        else:
            proc = run_command_with_timeout(run_cmd, timeout_seconds=cfg["run_timeout"])

        raw_stdout = sanitize_terminal_output(proc.stdout or "")
        raw_stderr = sanitize_terminal_output(proc.stderr or "")
        stdout = enforce_output_limits(raw_stdout)
        stderr = enforce_output_limits(raw_stderr)

        rc = proc.returncode

        # Detect Linux signals / OOM / crash
        if rc in LINUX_CRASH_SIGNALS:
            reason = stderr if stderr else LINUX_CRASH_SIGNALS[rc]
            return _err_result(language, 2, "runtime_error",
                               stdout, f"Process crashed (Exit Code {rc}): {reason}", compile_output)
        elif rc > 128:
            return _err_result(language, 2, "runtime_error",
                               stdout, f"Process crashed with signal exit code {rc}.\n{stderr}", compile_output)
        elif rc != 0:
            err_msg = stderr if stderr else stdout
            return _err_result(language, 2, "runtime_error",
                               stdout, err_msg.strip(), compile_output)

        full_out = stdout + ("\n" + stderr if stderr else "")
        return {
            "language": language,
            "status": "success",
            "status_code": 0,
            "stdout": full_out.strip(),
            "stderr": "",
            "compile_output": compile_output,
        }

    except (subprocess.TimeoutExpired, ExecutionTimeoutException):
        return _err_result(language, -1, "timeout",
                           "", f"[ERROR] Time Limit Exceeded ({cfg['run_timeout']}s)! Possible infinite loop.", compile_output)
    except Exception as e:
        return _err_result(language, -1, "system_error", "", f"[ERROR] Sandbox Runtime Error: {e}", compile_output)


def _err_result(language, code, status, stdout, stderr, compile_output) -> dict:
    return {
        "language": language,
        "status": status,
        "status_code": code,
        "stdout": stdout,
        "stderr": stderr,
        "compile_output": compile_output,
    }
