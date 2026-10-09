# ============================================================
# Hardened Java 21 Sandbox Image
# Mirrors C++ sandbox security posture exactly:
#   - Layer 3: Ephemeral Container Isolation
#   - Layer 6: Read-only Root Filesystem Ready
#   - Layer 7: Non-root Execution (sandboxuser UID 1000)
#   - Layer 8: Capability Restrictions Ready
# ============================================================
FROM eclipse-temurin:21-jdk-alpine

# Create unprivileged sandbox user (UID 1000) - mirrors cpp-sandbox
RUN adduser -D -u 1000 -s /bin/sh sandboxuser

# Create workspace directory
WORKDIR /sandbox

# Grant ownership to unprivileged user
RUN chown -R sandboxuser:sandboxuser /sandbox

# Default to unprivileged sandbox user
USER sandboxuser

CMD ["/bin/sh"]
