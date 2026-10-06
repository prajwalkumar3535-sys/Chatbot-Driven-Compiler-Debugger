# ============================================================
# Hardened C++ Compiler & LLDB Debugger Sandbox Image
# Security Layers Enforced:
# - Layer 3: Ephemeral Container Isolation
# - Layer 6: Read-only Root Filesystem Ready
# - Layer 7: Non-root Execution (sandboxuser UID 1000)
# - Layer 8: Capability Restrictions Ready
# ============================================================
FROM alpine:3.19

# Install minimal toolchain: GCC C++ compiler, LLDB debugger, Bash shell
RUN apk add --no-cache \
    g++ \
    lldb \
    libstdc++ \
    bash

# Create unprivileged sandbox user (UID 1000)
RUN adduser -D -u 1000 -s /bin/bash sandboxuser

# Create workspace directory
WORKDIR /sandbox

# Grant ownership to unprivileged user
RUN chown -R sandboxuser:sandboxuser /sandbox

# Default to unprivileged sandbox user
USER sandboxuser

CMD ["/bin/bash"]
