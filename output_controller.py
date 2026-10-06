"""
output_controller.py - Layer 10: Output Limits
Sanitizes and caps standard output (stdout) and standard error (stderr) streams.
Protects against:
  - Excessive output volume (programs printing GBs of log data)
  - Infinite printing loops overwhelming Streamlit / Web UI
  - Dangerous ANSI control sequences
"""

import re

# Output volume constraints
MAX_OUTPUT_BYTES = 50 * 1024  # 50 KB max output capture
MAX_OUTPUT_LINES = 1000       # 1,000 lines max output
TRUNCATION_NOTICE = "\n[⚠️ OUTPUT TRUNCATED: Program output exceeded 50KB limit]"

# Strip non-safe ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def enforce_output_limits(raw_text: str | bytes, max_bytes: int = MAX_OUTPUT_BYTES, max_lines: int = MAX_OUTPUT_LINES) -> str:
    """
    Limits the byte size and line count of program output, appending a notice if truncated.
    
    Returns:
        str: Cleaned, capped output string.
    """
    if raw_text is None:
        return ""

    if isinstance(raw_text, bytes):
        text = raw_text.decode('utf-8', errors='replace')
    else:
        text = str(raw_text)

    # Check byte size
    encoded = text.encode('utf-8', errors='replace')
    truncated = False

    if len(encoded) > max_bytes:
        text = encoded[:max_bytes].decode('utf-8', errors='ignore')
        truncated = True

    # Check line limit
    lines = text.splitlines()
    if len(lines) > max_lines:
        text = "\n".join(lines[:max_lines])
        truncated = True

    if truncated:
        text = text.rstrip() + TRUNCATION_NOTICE

    return text


def sanitize_terminal_output(text: str) -> str:
    """
    Strips raw terminal escape codes to prevent formatting corruption in web UI.
    """
    if not text:
        return ""
    return ANSI_ESCAPE_PATTERN.sub('', text)
