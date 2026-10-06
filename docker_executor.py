"""
docker_executor.py - Docker Sandbox Execution Engine
Coordinates Layers 3, 4, 5, 6, 7, 8, 9, 10, 11 to compile, run, and debug C++ code
inside a zero-trust, hardened container environment.

Enforces:
  - Layer 3: Docker Container Isolation
  - Layer 4: Zero Network Access (--network none)
  - Layer 5: Resource Limits (256MB RAM, 1.0 CPU)
  - Layer 6: Read-Only Filesystem (--read-only with isolated tmpfs)
  - Layer 7: Non-Root Execution (--user 1000:1000)
  - Layer 8: Capability Restrictions (--cap-drop ALL)
  - Layer 9: PID / Process Limits (--pids-limit 32)
  - Layer 10: Output Truncation & Sanitization
  - Layer 11: Execution Timeouts (5s run, 12s compile)
"""

import subprocess
import os
import shutil

from resource_controller import get_docker_resource_args, DEFAULT_COMPILE_MEMORY, DEFAULT_MEMORY_LIMIT
from output_controller import enforce_output_limits, sanitize_terminal_output
from timeout_controller import run_command_with_timeout, ExecutionTimeoutException, DEFAULT_COMPILE_TIMEOUT, DEFAULT_RUN_TIMEOUT, DEFAULT_LLDB_TIMEOUT

SANDBOX_IMAGE = "cpp-sandbox"
SANDBOX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox_env"))

LINUX_CRASH_SIGNALS = {
    139: "Segmentation Fault (SIGSEGV) - Invalid memory access / null pointer dereference",
    134: "Process Aborted (SIGABRT) - Assertion failed / double free / memory corruption",
    136: "Floating Point Exception (SIGFPE) - Division by zero",
    137: "Out of Memory (SIGKILL) - Memory limit exceeded (256MB cap)",
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


def compile_in_docker(sandbox_dir: str = SANDBOX_DIR, timeout: int = DEFAULT_COMPILE_TIMEOUT) -> tuple[int, str, str]:
    """
    Compiles C++ solution inside Docker container with strict resource caps.
    Returns: (status_code, stdout, stderr)
      0 = success
      1 = compilation error
     -1 = timeout / execution failure
    """
    os.makedirs(sandbox_dir, exist_ok=True)
    compile_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        *get_docker_resource_args(memory=DEFAULT_COMPILE_MEMORY, cpus="1.0", pids_limit=64),
        "-v", f"{sandbox_dir}:/sandbox",
        SANDBOX_IMAGE,
        "sh", "-c", "g++ -g /sandbox/solution.cpp -o /sandbox/prog"
    ]

    try:
        proc = run_command_with_timeout(compile_cmd, timeout_seconds=timeout)
        stdout = enforce_output_limits(sanitize_terminal_output(proc.stdout))
        stderr = enforce_output_limits(sanitize_terminal_output(proc.stderr))

        if proc.returncode != 0:
            return 1, stdout, stderr
        return 0, stdout, ""
    except ExecutionTimeoutException as exc:
        return -1, "", f"[ERROR] Compilation Time Limit Exceeded ({timeout}s)!"
    except Exception as e:
        return -1, "", f"[ERROR] Sandbox Compilation Error: {str(e)}"


def run_in_docker(sandbox_dir: str = SANDBOX_DIR, timeout: int = DEFAULT_RUN_TIMEOUT) -> tuple[int, str, str]:
    """
    Executes compiled binary inside Docker sandbox with:
      - --network none
      - --cap-drop ALL
      - --memory 256m
      - --pids-limit 32
      - --read-only with ephemeral /tmp tmpfs
      - --user 1000:1000
    
    Returns: (status_code, stdout, stderr)
      0 = success
      2 = runtime crash (segfault/abort/sigfpe)
     -1 = timeout (infinite loop)
    """
    run_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--cap-drop", "ALL",
        *get_docker_resource_args(memory=DEFAULT_MEMORY_LIMIT, cpus="1.0", pids_limit=32),
        "-v", f"{sandbox_dir}:/sandbox",
        SANDBOX_IMAGE,
        "/sandbox/prog"
    ]

    try:
        proc = run_command_with_timeout(run_cmd, timeout_seconds=timeout)
        raw_stdout = sanitize_terminal_output(proc.stdout)
        raw_stderr = sanitize_terminal_output(proc.stderr)

        stdout = enforce_output_limits(raw_stdout)
        stderr = enforce_output_limits(raw_stderr)

        # Catch Linux crash signal exit codes (128 + signal)
        if proc.returncode in LINUX_CRASH_SIGNALS:
            reason = stderr if stderr else LINUX_CRASH_SIGNALS[proc.returncode]
            return 2, stdout, f"Process crashed (Exit Code {proc.returncode}): {reason}"
        elif proc.returncode > 128:
            return 2, stdout, f"Process crashed with signal exit code {proc.returncode}.\n{stderr}"
        elif proc.returncode != 0:
            # User defined non-zero exit code
            full_out = stdout + ("\n" + stderr if stderr else "")
            return 0, full_out.strip(), ""

        full_out = stdout + ("\n" + stderr if stderr else "")
        return 0, full_out.strip(), ""

    except ExecutionTimeoutException as exc:
        return -1, "", f"[ERROR] Time Limit Exceeded ({timeout}s)! Possible infinite loop or blocking call."
    except Exception as e:
        return -1, "", f"[ERROR] Sandbox Runtime Error: {str(e)}"


def run_lldb_in_docker(sandbox_dir: str = SANDBOX_DIR, command: str = "bt", timeout: int = DEFAULT_LLDB_TIMEOUT) -> str:
    """
    Runs LLDB debugger inside sandbox container with SYS_PTRACE capability to inspect memory.
    """
    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--cap-add=SYS_PTRACE",
        "--security-opt", "seccomp=unconfined",
        *get_docker_resource_args(memory=DEFAULT_COMPILE_MEMORY, cpus="1.0", pids_limit=64),
        "-v", f"{sandbox_dir}:/sandbox",
        SANDBOX_IMAGE,
        "lldb", "-b",
        "-o", "settings set target.disable-aslr false",
        "-o", "run",
        "-o", command,
        "-o", "quit",
        "/sandbox/prog"
    ]

    try:
        proc = run_command_with_timeout(docker_cmd, timeout_seconds=timeout)
        raw_output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
        cleaned_lines = [
            line for line in raw_output.splitlines()
            if not line.startswith("Traceback") and
               not line.startswith("  File") and
               not line.startswith("ModuleNotFoundError")
        ]
        sanitized = sanitize_terminal_output("\n".join(cleaned_lines).strip())
        return enforce_output_limits(sanitized)
    except ExecutionTimeoutException:
        return f"LLDB Timeout: The command took longer than {timeout}s to execute in sandbox."
    except Exception as e:
        return f"LLDB Sandbox Error: {str(e)}"
