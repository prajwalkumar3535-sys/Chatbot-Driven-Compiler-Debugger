"""
timeout_controller.py - Layer 11: Execution Timeout
Enforces hard timeouts for compilation and execution phases to prevent infinite loops.
Protects against:
  - Infinite loops (while(true){})
  - Deadlocks and blocking I/O calls
  - Hanging compiler runs
"""

import subprocess
from typing import Any

# Default timeouts in seconds
DEFAULT_COMPILE_TIMEOUT = 12   # 12 seconds max for g++
DEFAULT_RUN_TIMEOUT = 5        # 5 seconds max for binary execution
DEFAULT_LLDB_TIMEOUT = 10      # 10 seconds max for LLDB session

class ExecutionTimeoutException(Exception):
    """Raised when a process exceeds its allowed execution window."""
    def __init__(self, message: str, timeout_seconds: int):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


def run_command_with_timeout(
    command: list[str],
    timeout_seconds: int = DEFAULT_RUN_TIMEOUT,
    cwd: str | None = None,
    capture_output: bool = True,
    text: bool = True
) -> subprocess.CompletedProcess[Any]:
    """
    Executes a shell command safely, terminating the process tree if the timeout expires.
    
    Raises:
        ExecutionTimeoutException: If time limit is exceeded.
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
            text=text,
            timeout=timeout_seconds
        )
        return result
    except subprocess.TimeoutExpired as exc:
        raise ExecutionTimeoutException(
            f"[ERROR] Time Limit Exceeded ({timeout_seconds}s)! Possible infinite loop or blocking call.",
            timeout_seconds=timeout_seconds
        ) from exc
