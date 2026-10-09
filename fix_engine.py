import re
from secure_scan import run_security_guardrail

def validate_ai_fix(llm_response: str, language: str = "cpp") -> tuple[bool, str | None, str]:
    """
    Extracts the code block from the LLM's response and scans it for vulnerabilities.
    Language-aware for C++, Python, and Java.
    Returns: (is_safe, extracted_code, security_warning)
    """
    lang = (language or "cpp").lower().strip()

    # 1. Extract the code block using regex
    if lang in ("python", "py"):
        match = re.search(r'```(?:python|py)?\n(.*?)\n```', llm_response, re.DOTALL | re.IGNORECASE)
    elif lang == "java":
        match = re.search(r'```(?:java)?\n(.*?)\n```', llm_response, re.DOTALL | re.IGNORECASE)
    else:
        match = re.search(r'```(?:cpp|c\+\+)?\n(.*?)\n```', llm_response, re.DOTALL | re.IGNORECASE)

    if not match:
        # Fallback to generic block
        match = re.search(r'```[a-zA-Z0-9_-]*\n(.*?)\n```', llm_response, re.DOTALL)
        if not match:
            return False, None, f"No valid {lang.upper()} code block was found in the AI suggestion."

    extracted_code = match.group(1).strip()

    # 2. Validate the AI-generated code for secure coding practices
    is_hard_blocked, block_msg, soft_warnings = run_security_guardrail(extracted_code, language=lang)

    if is_hard_blocked:
        return False, extracted_code, f"The AI suggested an insecure pattern: {block_msg}"

    # Build status message
    if soft_warnings:
        status = "The suggested fix is safe, but note: " + " | ".join(soft_warnings)
    else:
        status = "The suggested fix is secure."

    return True, extracted_code, status