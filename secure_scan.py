import re

# ============================================================
# LAYER 1: INPUT VALIDATION
# Guards against malformed, oversized, binary, or null-byte payloads
# before code reaches the regex scanner or compiler.
# ============================================================
MAX_CODE_SIZE_BYTES = 50 * 1024  # 50 KB max
MAX_LINE_COUNT = 2000

def validate_input(code_snippet):
    """
    Layer 1: Input Validation
    Protects against malformed, binary, oversized, or malicious non-text payloads.
    Returns: (is_valid: bool, error_message: str)
    """
    if not isinstance(code_snippet, str):
        return False, "Input validation error: Expected a valid text string."

    trimmed = code_snippet.strip()
    if not trimmed:
        return False, "Input validation error: Code is empty or contains only whitespace."

    encoded_bytes = code_snippet.encode('utf-8', errors='replace')
    if len(encoded_bytes) > MAX_CODE_SIZE_BYTES:
        return False, f"Input validation error: Payload exceeds maximum size ({len(encoded_bytes)} bytes > {MAX_CODE_SIZE_BYTES} bytes limit)."

    lines = code_snippet.splitlines()
    if len(lines) > MAX_LINE_COUNT:
        return False, f"Input validation error: Code exceeds maximum line count ({len(lines)} lines > {MAX_LINE_COUNT} lines limit)."

    if '\x00' in code_snippet:
        return False, "Input validation error: Malformed payload detected (Null-byte '\\0' injection)."

    control_char_count = sum(1 for ch in code_snippet if ord(ch) < 32 and ch not in ('\t', '\n', '\r'))
    if control_char_count > 0:
        return False, f"Input validation error: Malformed input contains {control_char_count} invalid binary/control character(s)."

    return True, ""

# ============================================================
# HARD BLOCKS: CRITICAL security issues that stop execution.
# These are dangerous enough to halt compilation entirely.
# ============================================================
_hard_block_patterns = {

    # 1. CRITICAL BUFFER OVERFLOWS
    r'\bgets\b': "CRITICAL: 'gets()' performs no bounds checking. It is officially removed from C++14. Use 'std::cin' or 'fgets()'.",
    r'\bstrcpy\b': "CRITICAL: 'strcpy' does not check buffer size. Use 'strncpy' or 'std::string'.",
    r'\bstrcat\b': "CRITICAL: 'strcat' can write past the end of a buffer. Use 'strncat' or 'std::string::append'.",
    r'\bsprintf\b': "CRITICAL: 'sprintf' lacks bounds checking. Use 'snprintf' to prevent overflows.",
    r'\bvsprintf\b': "CRITICAL: 'vsprintf' is unsafe. Use 'vsnprintf'.",
    r'\bwcscpy\b': "CRITICAL: Wide-character version of strcpy is equally unsafe. Use 'wcsncpy'.",
    r'\bwcscat\b': "CRITICAL: Wide-character version of strcat is unsafe. Use 'wcsncat'.",

    # 2. OS COMMAND INJECTION & PROCESS CONTROL
    r'\bsystem\s*\(': "CRITICAL: 'system()' allows arbitrary OS command execution. This is a severe injection vulnerability.",
    r'\bpopen\s*\(': "CRITICAL: 'popen()' opens a pipe to a shell command, which is vulnerable to injection attacks.",
    r'\bexecl\s*\(': "CRITICAL: The 'execl' function poses command injection risks. Validate all inputs before execution.",
    r'\bexecle\s*\(': "CRITICAL: The 'execle' function poses command injection risks.",
    r'\bexeclp\s*\(': "CRITICAL: The 'execlp' function poses command injection risks.",
    r'\bexecv\s*\(': "CRITICAL: The 'execv' function poses command injection risks.",
    r'\bexecvp\s*\(': "CRITICAL: The 'execvp' function poses command injection risks.",
    r'\bexecve\s*\(': "CRITICAL: The 'execve' function poses command injection risks.",

    # 3. FORMAT STRING VULNERABILITIES
    r'\bprintf\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)': "CRITICAL: Format string vulnerability. Never pass a variable directly to 'printf'. Use 'printf(\"%s\", var)'.",
    r'\bfprintf\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)': "CRITICAL: Format string vulnerability in 'fprintf'. Ensure the format string is hardcoded.",

    # 4. INSECURE TEMPORARY FILE CREATION
    r'\bmktemp\s*\(': "CRITICAL: 'mktemp' suffers from race conditions. Use 'mkstemp' instead.",
    r'\btmpnam\s*\(': "CRITICAL: 'tmpnam' is obsolete and insecure. Use 'mkstemp'.",
    r'\btempnam\s*\(': "CRITICAL: 'tempnam' is vulnerable to race conditions. Use 'mkstemp'.",

    # 5. DEPRECATED / UNSAFE C++ MEMORY MANAGEMENT
    r'\bauto_ptr\b': "CRITICAL: 'std::auto_ptr' is deprecated in C++11 and removed in C++17 due to unsafe copy semantics. Use 'std::unique_ptr'.",
}

# ============================================================
# SOFT WARNINGS: Bad practices worth flagging, but NOT severe
# enough to stop compilation. These are shown as chatbot
# advisory messages and code still compiles and runs.
# ============================================================
_soft_warning_patterns = {

    # Coding practice issues
    r'\bstrncpy\b': "WARNING: 'strncpy' can leave strings unterminated if the source is larger than the destination. Prefer 'std::string'.",
    r'\bsyslog\s*\(': "WARNING: Ensure you are not passing un-sanitized user input directly to 'syslog()'.",
    r'\bfree\s*\(': "WARNING: Mixing 'malloc/free' with 'new/delete' causes undefined behavior. Stick to C++ paradigms (new/delete or smart pointers).",
    r'\bdelete\s+': "WARNING: Manual 'delete' can lead to dangling pointers. Modern C++ heavily favors 'std::unique_ptr' or 'std::shared_ptr'.",
    r'\bscanf\s*\(\s*\"%s\"': "RISK: 'scanf' with '%s' has no bounds checking. Specify a width (e.g., '%49s') or use 'std::cin'.",

    # Weak randomness
    r'\brand\s*\(\s*\)': "WARNING: 'rand()' is not cryptographically secure. For security-sensitive randomness, use the '<random>' library (e.g., std::mt19937).",
    r'\bsrand\s*\(': "WARNING: Seeding with 'srand(time(NULL))' is predictable. Use a true hardware entropy source like 'std::random_device'.",

    # Platform & standard issues
    r'system\s*\(\s*\"pause\"\s*\)': "WARNING: 'system(\"pause\")' is platform-dependent (Windows only). Use 'std::cin.get()' for cross-platform compatibility.",
    r'\bvoid\s+main\b': "STANDARD: 'void main()' is non-standard C++. The standard dictates using 'int main()' and returning 0.",

    # Performance advisory (does NOT block — common in competitive programming)
    r'#include\s+<bits/stdc\+\+\.h>': "ADVISORY: Including '<bits/stdc++.h>' increases compilation time and is non-portable. Consider including only the specific headers you need (e.g., <iostream>, <vector>). Your code will still compile.",
}


def run_security_guardrail(code_snippet):
    """
    Scans the provided code for security issues.
    Returns: (is_hard_blocked: bool, block_message: str, soft_warnings: list[str])
      - is_hard_blocked=True  → stop execution, show error
      - is_hard_blocked=False → proceed, but show any soft_warnings in chatbot
    """
    # 0. Layer 1: Input Validation Check
    is_valid, err_msg = validate_input(code_snippet)
    if not is_valid:
        return True, f"INPUT VALIDATION REJECTED: {err_msg}", []

    # 1. Check hard blocks first — stop immediately on first match
    for pattern, message in _hard_block_patterns.items():
        if re.search(pattern, code_snippet):
            return True, message, []

    # 2. Collect all soft warnings — never stop execution
    soft_warnings = []
    for pattern, message in _soft_warning_patterns.items():
        if re.search(pattern, code_snippet):
            soft_warnings.append(message)

    return False, "", soft_warnings