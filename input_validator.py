"""
input_validator.py - Layer 1: Input Validation
Validates user-submitted source code and input before passing to static scanners or compilers.
Supports C++, Python, and Java.

Protects against:
  - Unsupported language requests
  - Malformed / binary payloads
  - Oversized payloads (DoS)
  - Excessive line counts
  - Null-byte injections (\0 / \x00)
  - Oversized or malformed stdin payloads
"""

from language_config import ALLOWED_LANGUAGES, validate_language

# Default thresholds
MAX_CODE_SIZE_BYTES = 50 * 1024  # 50 KB max
MAX_STDIN_SIZE_BYTES = 10 * 1024 # 10 KB max
MAX_LINE_COUNT = 2000            # 2,000 lines max
MIN_CODE_LENGTH = 1              # Minimum non-whitespace characters


def validate_input(code_snippet: str, max_bytes: int = MAX_CODE_SIZE_BYTES, max_lines: int = MAX_LINE_COUNT, language: str | None = None) -> tuple[bool, str]:
    """
    Validates the raw input code snippet against malformed or oversized payload attacks.
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if input passes all checks, False otherwise.
            - error_message: Empty string if valid, otherwise description of violation.
    """
    # 0. Language check if supplied
    if language is not None:
        is_valid_lang, lang_err = validate_language(language)
        if not is_valid_lang:
            return False, f"Input validation error: {lang_err}"

    # 1. Type validation
    if not isinstance(code_snippet, str):
        return False, "Input validation error: Expected a valid text string."

    # 2. Empty / Whitespace validation
    trimmed = code_snippet.strip()
    if len(trimmed) < MIN_CODE_LENGTH:
        return False, "Input validation error: Code is empty or contains only whitespace."

    # 3. Payload size check (Bytes)
    encoded_bytes = code_snippet.encode('utf-8', errors='replace')
    if len(encoded_bytes) > max_bytes:
        return False, f"Input validation error: Payload exceeds maximum size ({len(encoded_bytes)} bytes > {max_bytes} bytes limit)."

    # 4. Line count check
    lines = code_snippet.splitlines()
    if len(lines) > max_lines:
        return False, f"Input validation error: Code exceeds maximum line count ({len(lines)} lines > {max_lines} lines limit)."

    # 5. Null-byte injection check
    if '\x00' in code_snippet or '\0' in code_snippet:
        return False, "Input validation error: Malformed payload detected (Null-byte '\\0' injection)."

    # 6. Binary / Non-printable control character check (excluding standard \t, \n, \r)
    control_char_count = sum(1 for ch in code_snippet if ord(ch) < 32 and ch not in ('\t', '\n', '\r'))
    if control_char_count > 0:
        return False, f"Input validation error: Malformed input contains {control_char_count} invalid binary/control character(s)."

    return True, ""


def validate_stdin(stdin_snippet: str, max_bytes: int = MAX_STDIN_SIZE_BYTES) -> tuple[bool, str]:
    """
    Validates stdin input sent to programs.
    """
    if not isinstance(stdin_snippet, str):
        return False, "Stdin validation error: Expected a text string."
    
    encoded_bytes = stdin_snippet.encode('utf-8', errors='replace')
    if len(encoded_bytes) > max_bytes:
        return False, f"Stdin validation error: Stdin exceeds limit ({len(encoded_bytes)} bytes > {max_bytes} bytes limit)."

    if '\x00' in stdin_snippet:
        return False, "Stdin validation error: Null-byte injection in stdin payload."

    return True, ""


def validate_execution_request(language: str, code: str, stdin_data: str = "") -> tuple[bool, str]:
    """
    Unified validation for an execution request.
    Validates language, code payload, and optional stdin data.
    """
    # 1. Language validation
    is_valid_lang, lang_err = validate_language(language)
    if not is_valid_lang:
        return False, lang_err

    # 2. Source code validation
    is_valid_code, code_err = validate_input(code, language=language)
    if not is_valid_code:
        return False, code_err

    # 3. Stdin validation
    if stdin_data:
        is_valid_stdin, stdin_err = validate_stdin(stdin_data)
        if not is_valid_stdin:
            return False, stdin_err

    return True, ""


def sanitize_input(code_snippet: str) -> str:
    """
    Normalizes line endings to standard LF (\n).
    """
    if not isinstance(code_snippet, str):
        return ""
    return code_snippet.replace('\r\n', '\n').replace('\r', '\n')
