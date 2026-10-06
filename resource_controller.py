"""
resource_controller.py - Layer 5: Resource Limits & Layer 9: Process/PID Limits
Configures and enforces hardware constraints and process quotas for sandboxed execution.
Protects against:
  - Fork bombs (thousands of spawned processes)
  - Memory exhaustion (RAM hogging)
  - CPU starvation / 100% CPU lockups
"""

# Default sandbox resource limits
DEFAULT_MEMORY_LIMIT = "256m"       # 256 MB RAM cap
DEFAULT_COMPILE_MEMORY = "512m"     # 512 MB for compiler
DEFAULT_CPU_LIMIT = "1.0"           # 1.0 CPU Core max
DEFAULT_PID_LIMIT = 32              # Max 32 active processes/threads
DEFAULT_SWAP_LIMIT = "256m"         # Disable additional swap expansion

def get_docker_resource_args(
    memory: str = DEFAULT_MEMORY_LIMIT,
    cpus: str = DEFAULT_CPU_LIMIT,
    pids_limit: int = DEFAULT_PID_LIMIT,
    memory_swap: str | None = None
) -> list[str]:
    """
    Returns Docker CLI arguments enforcing memory, CPU, and PID limits.
    """
    args = [
        f"--memory={memory}",
        f"--cpus={cpus}",
        f"--pids-limit={pids_limit}",
    ]
    # In Docker, memory-swap must be >= memory. If not specified, set equal to memory (disables extra swap).
    swap_val = memory_swap if memory_swap else memory
    if swap_val:
        args.append(f"--memory-swap={swap_val}")
    return args


def get_resource_config() -> dict[str, str | int]:
    """
    Returns current active resource policy summary.
    """
    return {
        "memory_limit": DEFAULT_MEMORY_LIMIT,
        "compile_memory_limit": DEFAULT_COMPILE_MEMORY,
        "cpu_quota": DEFAULT_CPU_LIMIT,
        "pids_limit": DEFAULT_PID_LIMIT,
        "memory_swap": DEFAULT_SWAP_LIMIT
    }
