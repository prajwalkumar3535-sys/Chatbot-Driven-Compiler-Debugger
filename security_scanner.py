"""
security_scanner.py - Layer 2: Static Security Scanner & Layer 12: AI Fix Verification
Performs static analysis on source code and AI-generated repair fixes for C++, Python, and Java.

Protects against:
  - OS Command Injections (system, popen, exec*, subprocess, Runtime.exec, ProcessBuilder)
  - Buffer Overflows & Memory Corruption (gets, strcpy, strcat, sprintf, vsprintf)
  - Format String Attacks (printf with variable format string)
  - Insecure Temporary File Creation (mktemp, tmpnam, tempnam)
  - Unsafe / Deprecated idioms (auto_ptr, void main, Unsafe)
  - Unauthorized network attempts and sensitive path access
"""

import re
from input_validator import validate_input

# ============================================================
# C++ PATTERNS
# ============================================================
CPP_HARD_BLOCK_PATTERNS = {
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

CPP_SOFT_WARNING_PATTERNS = {
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

# Alias for backward compatibility
HARD_BLOCK_PATTERNS = CPP_HARD_BLOCK_PATTERNS
SOFT_WARNING_PATTERNS = CPP_SOFT_WARNING_PATTERNS

# ============================================================
# PYTHON PATTERNS
# ============================================================
PYTHON_HARD_BLOCK_PATTERNS = {
    # 1. OS Command Injection & Process Spawning
    r'\bos\.system\s*\(': "CRITICAL: 'os.system()' allows arbitrary OS command execution.",
    r'\bos\.popen\s*\(': "CRITICAL: 'os.popen()' allows arbitrary command execution via pipes.",
    r'\bos\.spawn[a-zA-Z]*\s*\(': "CRITICAL: 'os.spawn*' spawns arbitrary OS processes.",
    r'\bos\.exec[a-zA-Z]*\s*\(': "CRITICAL: 'os.exec*' replaces current process with arbitrary OS binary.",
    r'\bsubprocess\.(?:Popen|run|call|check_output|check_call)\s*\(': "CRITICAL: 'subprocess' process creation is disallowed in sandbox submissions.",
    r'\bpty\.spawn\s*\(': "CRITICAL: 'pty.spawn' allows pseudo-terminal escalation.",

    # 2. Code Injection & Dynamic Execution
    r'\beval\s*\(': "CRITICAL: 'eval()' allows arbitrary dynamic Python expression execution.",
    r'\bexec\s*\(': "CRITICAL: 'exec()' allows arbitrary dynamic Python statement execution.",
    r'__import__\s*\(\s*[\'"](?:os|subprocess|pty|socket)[\'"]': "CRITICAL: Dynamic import of restricted system modules is prohibited.",

    # 3. Network operations (static guardrail)
    r'\bimport\s+socket\b': "CRITICAL: Network socket operations are prohibited in sandbox.",
    r'\bfrom\s+socket\s+import\b': "CRITICAL: Network socket operations are prohibited in sandbox.",
    r'\bsocket\.socket\s*\(': "CRITICAL: Network socket creation is blocked.",
    r'\burllib\.request\b': "CRITICAL: Network requests via urllib are prohibited.",
    r'\bhttp\.client\b': "CRITICAL: Network requests via http.client are prohibited.",
    r'\brequests\.(?:get|post|put|delete)\s*\(': "CRITICAL: HTTP network requests via 'requests' are prohibited.",

    # 4. Sensitive filesystem locations
    r'open\s*\(\s*[\'"]\/(?:etc|proc|sys|root)': "CRITICAL: Access to sensitive system directories (/etc, /proc, /sys, /root) is forbidden.",
    r'shutil\.rmtree\s*\(\s*[\'"]\/[\'"]': "CRITICAL: Destructive filesystem operations are strictly forbidden.",
}

PYTHON_SOFT_WARNING_PATTERNS = {
    r'except\s*:': "WARNING: Bare 'except:' catches all exceptions including SystemExit and KeyboardInterrupt. Prefer 'except Exception:'.",
    r'from\s+\w+\s+import\s+\*': "WARNING: Wildcard 'import *' pollutes namespace. Import explicit names instead.",
    r'time\.sleep\s*\(\s*(?:[1-9]\d{1,})\s*\)': "WARNING: Long sleep duration may trigger execution timeout (5s limit).",
}

# ============================================================
# JAVA PATTERNS
# ============================================================
JAVA_HARD_BLOCK_PATTERNS = {
    # 1. Process Execution
    r'Runtime\.getRuntime\s*\(\s*\)\.exec\s*\(': "CRITICAL: 'Runtime.getRuntime().exec()' allows arbitrary command execution.",
    r'new\s+ProcessBuilder\s*\(': "CRITICAL: 'ProcessBuilder' allows arbitrary process execution.",
    r'ProcessBuilder\s*\(': "CRITICAL: 'ProcessBuilder' allows arbitrary process execution.",
    r'System\.exit\s*\(': "CRITICAL: 'System.exit()' terminates the JVM runtime.",

    # 2. Native code & Unsafe reflection
    r'System\.loadLibrary\s*\(': "CRITICAL: Loading native libraries via 'System.loadLibrary()' is prohibited.",
    r'System\.load\s*\(': "CRITICAL: Loading native binaries via 'System.load()' is prohibited.",
    r'sun\.misc\.Unsafe': "CRITICAL: 'sun.misc.Unsafe' low-level memory access is prohibited.",

    # 3. Network operations
    r'java\.net\.Socket\b': "CRITICAL: Network socket operations are prohibited in sandbox.",
    r'java\.net\.ServerSocket\b': "CRITICAL: Server sockets are prohibited in sandbox.",
    r'java\.net\.URL\b': "CRITICAL: Network URL operations are prohibited in sandbox.",
    r'HttpURLConnection\b': "CRITICAL: HTTP connections are prohibited in sandbox.",

    # 4. Sensitive system paths
    r'new\s+File(?:InputStream|Reader)?\s*\(\s*[\'"]\/(?:etc|proc|sys|root)': "CRITICAL: Access to sensitive system directories is forbidden.",
}

JAVA_SOFT_WARNING_PATTERNS = {
    r'System\.gc\s*\(\s*\)': "WARNING: Explicit 'System.gc()' calls are usually unnecessary and degrade performance.",
    r'Thread\.stop\s*\(\s*\)': "WARNING: 'Thread.stop()' is deprecated and inherently unsafe.",
    r'\.printStackTrace\s*\(\s*\)': "WARNING: 'printStackTrace()' outputs raw stack traces. Consider using structured logging.",
}


def get_patterns_for_language(language: str = "cpp") -> tuple[dict, dict]:
    """Returns (hard_blocks, soft_warnings) for given language."""
    lang = (language or "cpp").lower().strip()
    if lang == "python" or lang == "py":
        return PYTHON_HARD_BLOCK_PATTERNS, PYTHON_SOFT_WARNING_PATTERNS
    elif lang == "java":
        return JAVA_HARD_BLOCK_PATTERNS, JAVA_SOFT_WARNING_PATTERNS
    else:
        return CPP_HARD_BLOCK_PATTERNS, CPP_SOFT_WARNING_PATTERNS


def scan_code(code_snippet: str, language: str = "cpp") -> tuple[bool, str, list[str]]:
    """
    Scans source code using Layer 1 (Input Validation) & Layer 2 (Static Guardrails).
    Language-aware for C++, Python, and Java.
    
    Returns:
        tuple[bool, str, list[str]]: (is_blocked, block_message, soft_warnings)
          - is_blocked=True: Stop execution, block_message contains critical reason.
          - is_blocked=False: Proceed to execution sandbox.
    """
    # 0. Input validation check
    is_valid, val_err = validate_input(code_snippet, language=language)
    if not is_valid:
        return True, f"Input Validation Failed: {val_err}", []

    hard_blocks, soft_warnings_dict = get_patterns_for_language(language)

    # 1. Hard block checks
    for pattern, msg in hard_blocks.items():
        if re.search(pattern, code_snippet):
            return True, msg, []

    # 2. Soft warning checks
    soft_warnings = []
    for pattern, msg in soft_warnings_dict.items():
        if re.search(pattern, code_snippet):
            soft_warnings.append(msg)

    return False, "", soft_warnings


def verify_ai_fix(llm_response: str, language: str = "cpp") -> tuple[bool, str | None, str]:
    """
    Layer 12: AI Fix Security Verification.
    Validates that LLM generated code repairs do not introduce security risks.
    Language-aware for C++, Python, and Java.
    
    Returns:
        tuple[bool, str | None, str]: (is_safe, extracted_code, status_message)
    """
    lang = (language or "cpp").lower().strip()
    
    # Extract code from markdown block matching language
    if lang in ("python", "py"):
        match = re.search(r'```(?:python|py)?\n(.*?)\n```', llm_response, re.DOTALL | re.IGNORECASE)
    elif lang == "java":
        match = re.search(r'```(?:java)?\n(.*?)\n```', llm_response, re.DOTALL | re.IGNORECASE)
    else:
        match = re.search(r'```(?:cpp|c\+\+)?\n(.*?)\n```', llm_response, re.DOTALL | re.IGNORECASE)

    if not match:
        # Fallback to any code block
        match = re.search(r'```[a-zA-Z0-9_-]*\n(.*?)\n```', llm_response, re.DOTALL)
        if not match:
            return False, None, f"No valid {language.upper()} code block was found in the AI suggestion."

    extracted_code = match.group(1).strip()
    is_blocked, block_msg, soft_warnings = scan_code(extracted_code, language=language)

    if is_blocked:
        return False, extracted_code, f"Security Violation: AI suggested an unsafe pattern: {block_msg}"

    if soft_warnings:
        status_msg = "The suggested fix is safe, but note: " + " | ".join(soft_warnings)
    else:
        status_msg = "The suggested fix passed all security verification checks."

    return True, extracted_code, status_msg
