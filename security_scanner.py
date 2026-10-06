"""
security_scanner.py - Layer 2: Static Security Scanner & Layer 12: AI Fix Verification
Performs static analysis on C++ source code and AI-generated repair fixes.
Protects against:
  - OS Command Injections (system, popen, exec*)
  - Buffer Overflows & Memory Corruption (gets, strcpy, strcat, sprintf, vsprintf)
  - Format String Attacks (printf with variable format string)
  - Insecure Temporary File Creation (mktemp, tmpnam, tempnam)
  - Unsafe / Deprecated C++ idioms (auto_ptr, void main)
"""

import re
from input_validator import validate_input

# ============================================================
# HARD BLOCKS: CRITICAL security threats that halt execution
# ============================================================
HARD_BLOCK_PATTERNS = {
    # 1. Critical Buffer Overflows
    r'\bgets\b': "CRITICAL: 'gets()' performs no bounds checking. It is officially removed in C++14. Use 'std::cin' or 'fgets()'.",
    r'\bstrcpy\b': "CRITICAL: 'strcpy' does not check buffer size. Use 'strncpy' or 'std::string'.",
    r'\bstrcat\b': "CRITICAL: 'strcat' can write past the end of a buffer. Use 'strncat' or 'std::string::append'.",
    r'\bsprintf\b': "CRITICAL: 'sprintf' lacks bounds checking. Use 'snprintf' to prevent overflows.",
    r'\bvsprintf\b': "CRITICAL: 'vsprintf' is unsafe. Use 'vsnprintf'.",
    r'\bwcscpy\b': "CRITICAL: Wide-character version of strcpy is unsafe. Use 'wcsncpy'.",
    r'\bwcscat\b': "CRITICAL: Wide-character version of strcat is unsafe. Use 'wcsncat'.",

    # 2. OS Command Injection & Process Spawning
    r'\bsystem\s*\(': "CRITICAL: 'system()' allows arbitrary OS command execution. Severe command injection vulnerability.",
    r'\bpopen\s*\(': "CRITICAL: 'popen()' opens a pipe to a shell command, vulnerable to injection attacks.",
    r'\bexecl\s*\(': "CRITICAL: 'execl' poses process injection risks. Validate all inputs before execution.",
    r'\bexecle\s*\(': "CRITICAL: 'execle' poses process injection risks.",
    r'\bexeclp\s*\(': "CRITICAL: 'execlp' poses process injection risks.",
    r'\bexecv\s*\(': "CRITICAL: 'execv' poses process injection risks.",
    r'\bexecvp\s*\(': "CRITICAL: 'execvp' poses process injection risks.",
    r'\bexecve\s*\(': "CRITICAL: 'execve' poses process injection risks.",

    # 3. Format String Vulnerabilities
    r'\bprintf\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)': "CRITICAL: Format string vulnerability. Never pass a variable directly as format string. Use 'printf(\"%s\", var)'.",
    r'\bfprintf\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\)': "CRITICAL: Format string vulnerability in 'fprintf'. Ensure format string is hardcoded.",

    # 4. Insecure Temporary File Creation (Race Conditions)
    r'\bmktemp\s*\(': "CRITICAL: 'mktemp' suffers from race conditions. Use 'mkstemp' instead.",
    r'\btmpnam\s*\(': "CRITICAL: 'tmpnam' is obsolete and insecure. Use 'mkstemp'.",
    r'\btempnam\s*\(': "CRITICAL: 'tempnam' is vulnerable to race conditions. Use 'mkstemp'.",

    # 5. Deprecated / Unsafe Memory Management
    r'\bauto_ptr\b': "CRITICAL: 'std::auto_ptr' is removed in C++17 due to unsafe copy semantics. Use 'std::unique_ptr'.",
}

# ============================================================
# SOFT WARNINGS: Code advisories (flagged but allowed to compile)
# ============================================================
SOFT_WARNING_PATTERNS = {
    r'\bstrncpy\b': "WARNING: 'strncpy' can leave strings unterminated if source is larger than destination. Prefer 'std::string'.",
    r'\bsyslog\s*\(': "WARNING: Ensure you are not passing un-sanitized user input directly to 'syslog()'.",
    r'\bfree\s*\(': "WARNING: Mixing 'malloc/free' with 'new/delete' causes undefined behavior. Stick to C++ smart pointers or new/delete.",
    r'\bdelete\s+': "WARNING: Manual 'delete' can lead to dangling pointers or double frees. Modern C++ favors 'std::unique_ptr' or 'std::shared_ptr'.",
    r'\bscanf\s*\(\s*\"%s\"': "RISK: 'scanf' with '%s' has no bounds checking. Specify a width (e.g., '%49s') or use 'std::cin'.",
    r'\brand\s*\(\s*\)': "WARNING: 'rand()' is not cryptographically secure. Use '<random>' (e.g., std::mt19937) for secure randomness.",
    r'\bsrand\s*\(': "WARNING: Seeding with 'srand(time(NULL))' is predictable. Use hardware entropy via 'std::random_device'.",
    r'system\s*\(\s*\"pause\"\s*\)': "WARNING: 'system(\"pause\")' is platform-dependent (Windows only). Use 'std::cin.get()'.",
    r'\bvoid\s+main\b': "STANDARD: 'void main()' is non-standard C++. Use 'int main()' and return 0.",
    r'#include\s+<bits/stdc\+\+\.h>': "ADVISORY: '<bits/stdc++.h>' is non-portable and increases compilation time. Include specific headers (e.g. <iostream>, <vector>).",
}


def scan_code(code_snippet: str) -> tuple[bool, str, list[str]]:
    """
    Scans C++ source code using Layer 1 (Input Validation) & Layer 2 (Static Guardrails).
    
    Returns:
        tuple[bool, str, list[str]]: (is_blocked, block_message, soft_warnings)
          - is_blocked=True: Stop execution, block_message contains critical reason.
          - is_blocked=False: Proceed to execution sandbox.
    """
    # 0. Input validation check
    is_valid, val_err = validate_input(code_snippet)
    if not is_valid:
        return True, f"Input Validation Failed: {val_err}", []

    # 1. Hard block checks
    for pattern, msg in HARD_BLOCK_PATTERNS.items():
        if re.search(pattern, code_snippet):
            return True, msg, []

    # 2. Soft warning checks
    soft_warnings = []
    for pattern, msg in SOFT_WARNING_PATTERNS.items():
        if re.search(pattern, code_snippet):
            soft_warnings.append(msg)

    return False, "", soft_warnings


def verify_ai_fix(llm_response: str) -> tuple[bool, str | None, str]:
    """
    Layer 12: AI Fix Security Verification.
    Validates that LLM generated code repairs do not introduce security risks.
    
    Returns:
        tuple[bool, str | None, str]: (is_safe, extracted_code, status_message)
    """
    # Extract code from markdown block
    match = re.search(r'```(?:cpp|c\+\+)?\n(.*?)\n```', llm_response, re.DOTALL | re.IGNORECASE)
    if not match:
        return False, None, "No valid C++ code block was found in the AI suggestion."

    extracted_code = match.group(1).strip()
    is_blocked, block_msg, soft_warnings = scan_code(extracted_code)

    if is_blocked:
        return False, extracted_code, f"Security Violation: AI suggested an unsafe pattern: {block_msg}"

    if soft_warnings:
        status_msg = "The suggested fix is safe, but note: " + " | ".join(soft_warnings)
    else:
        status_msg = "The suggested fix passed all security verification checks."

    return True, extracted_code, status_msg
