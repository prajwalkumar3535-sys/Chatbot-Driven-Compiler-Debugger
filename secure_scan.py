"""
secure_scan.py - Layer 1 & 2 Security Guardrails
Provides input validation and static security pre-scanning for C++, Python, and Java.
"""

from input_validator import validate_input
from security_scanner import scan_code, get_patterns_for_language, CPP_HARD_BLOCK_PATTERNS, CPP_SOFT_WARNING_PATTERNS

# Backward compatible patterns
_hard_block_patterns = CPP_HARD_BLOCK_PATTERNS
_soft_warning_patterns = CPP_SOFT_WARNING_PATTERNS


def run_security_guardrail(code_snippet: str, language: str = "cpp") -> tuple[bool, str, list[str]]:
    """
    Scans the provided code for security issues and malformed input.
    Language-aware for C++, Python, and Java.

    Returns: (is_hard_blocked: bool, block_message: str, soft_warnings: list[str])
      - is_hard_blocked=True  → stop execution, show error
      - is_hard_blocked=False → proceed, but show any soft_warnings in chatbot
    """
    return scan_code(code_snippet, language=language)