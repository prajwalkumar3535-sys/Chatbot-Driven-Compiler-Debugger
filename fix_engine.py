import re
from typing import Optional
from secure_scan import run_security_guardrail
from code_reconstructor import reconstruct_full_code

def validate_ai_fix(llm_response: str, language: str = "cpp", original_code: Optional[str] = None) -> tuple[bool, str | None, str]:
    """
    Extracts the code block from the LLM's response, splices it into original_code
    (ensuring massive 5,000+ line codebases remain 100% complete), and scans for vulnerabilities.
    Returns: (is_safe, full_reconstructed_code, security_warning)
    """
    lang = (language or "cpp").lower().strip()

    # 1. Extract the code block using regex (supports closed and unclosed trailing code blocks)
    pattern = re.compile(r'```(?:' + re.escape(lang) + r'|cpp|c\+\+|python|py|java)?\n(.*?)(?:\n```|$)', re.DOTALL | re.IGNORECASE)
    match = pattern.search(llm_response)

    if not match:
        # Fallback to generic code block
        match = re.search(r'```[a-zA-Z0-9_-]*\n(.*?)(?:\n```|$)', llm_response, re.DOTALL)
        if not match:
            return False, None, f"No valid {lang.upper()} code block was found in the AI suggestion."

    extracted_code = match.group(1).strip()
    if not extracted_code:
        return False, None, f"Empty code block returned in {lang.upper()} suggestion."

    # If original_code is supplied (e.g. a 5,000-line codebase), reconstruct the full file
    if original_code and original_code.strip():
        final_code = reconstruct_full_code(original_code, extracted_code, language=lang)
    else:
        final_code = extracted_code

    # 2. Validate the code for secure coding practices
    is_hard_blocked, block_msg, soft_warnings = run_security_guardrail(final_code, language=lang)

    if is_hard_blocked:
        return False, final_code, f"The AI suggested an insecure pattern: {block_msg}"

    # Build status message
    if soft_warnings:
        status = "The suggested fix is safe, but note: " + " | ".join(soft_warnings)
    else:
        status = "The suggested fix is secure."

    return True, final_code, status