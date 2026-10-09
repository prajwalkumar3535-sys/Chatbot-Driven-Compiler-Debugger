# ============================================================
# Unified Multi-Language Sandbox Image
# Contains: G++, Python 3, Java 21 JDK, LLDB
# Based on cpp-sandbox (Alpine 3.19) — no internet needed.
# Security Layers:
#   - Layer 3: Ephemeral Container Isolation
#   - Layer 6: Read-only Root Filesystem Ready
#   - Layer 7: Non-root Execution (sandboxuser UID 1000)
#   - Layer 8: Capability Restrictions Ready
# ============================================================
FROM cpp-sandbox:latest

# Switch to root briefly to install Python and Java
USER root

# Install Python 3 and Java 21 JDK
RUN apk add --no-cache \
    python3 \
    py3-pip \
    openjdk21-jdk

# Switch back to non-root sandbox user
USER sandboxuser

CMD ["/bin/bash"]
