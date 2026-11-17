"""
code_reconstructor.py - Seamless Surgical Splicer & Full-Code Reconstructor
Handles massive codebases (up to 5,000+ lines).
When a local LLM returns a targeted fix, a single function, a patched scope,
or code with placeholder comments ('// ... rest of code ...'), this module
intelligently splices the fix into the original codebase, ensuring the user
always receives the 100% complete, fully working 5,000+ line code.
"""

import re
import ast
from typing import Optional, Tuple, List

PLACEHOLDER_PATTERNS = [
    re.compile(r'^\s*//\s*\.\.\..*$', re.MULTILINE),
    re.compile(r'^\s*//\s*\[\s*rest of (?:the )?code.*?\].*$', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^\s*//\s*remaining code.*$', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^\s*/\*\s*\.\.\..*?\*/', re.DOTALL),
    re.compile(r'^\s*#\s*\.\.\..*$', re.MULTILINE),
    re.compile(r'^\s*#\s*\[\s*rest of (?:the )?code.*?\].*$', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^\s*#\s*remaining code.*$', re.MULTILINE | re.IGNORECASE),
]

def has_placeholder(code: str) -> bool:
    """Checks whether the code contains '// ...' or '# ...' placeholder comments."""
    for p in PLACEHOLDER_PATTERNS:
        if p.search(code):
            return True
    return False

def clean_placeholders(code: str) -> str:
    """Removes placeholder comments from code."""
    res = code
    for p in PLACEHOLDER_PATTERNS:
        res = p.sub("", res)
    return res.strip()

def _find_brace_matching_block(source: str, start_brace_idx: int) -> int:
    """Returns the index of the closing brace matching the opening brace at start_brace_idx."""
    depth = 0
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    i = start_brace_idx
    n = len(source)

    while i < n:
        c = source[i]
        nxt = source[i + 1] if i + 1 < n else ''

        if in_line_comment:
            if c == '\n':
                in_line_comment = False
        elif in_block_comment:
            if c == '*' and nxt == '/':
                in_block_comment = False
                i += 1
        elif in_string:
            if c == '\\':
                i += 1
            elif c == '"':
                in_string = False
        elif in_char:
            if c == '\\':
                i += 1
            elif c == "'":
                in_char = False
        else:
            if c == '/' and nxt == '/':
                in_line_comment = True
                i += 1
            elif c == '/' and nxt == '*':
                in_block_comment = True
                i += 1
            elif c == '"':
                in_string = True
            elif c == "'":
                in_char = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1

def _splice_cpp_function(original_code: str, func_name: str, new_func_code: str) -> Optional[str]:
    """Finds func_name in original_code and replaces its entire definition with new_func_code."""
    pattern = re.compile(
        r'(?:^[ \t]*(?:template\s*<[^>]*>\s*)?(?:inline|static|virtual|explicit|constexpr|friend)?\s*[\w:<>\*&]+\s+)?\b'
        + re.escape(func_name)
        + r'\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*\{',
        re.MULTILINE
    )
    
    match = pattern.search(original_code)
    if not match:
        return None

    brace_start = match.end() - 1
    brace_end = _find_brace_matching_block(original_code, brace_start)
    if brace_end == -1:
        return None

    # Replace from start of function declaration to brace_end
    func_start = match.start()
    return original_code[:func_start] + new_func_code.strip() + original_code[brace_end + 1:]

def _splice_python_function(original_code: str, func_name: str, new_func_code: str) -> Optional[str]:
    """Finds def func_name(...) in Python source and replaces it."""
    lines = original_code.splitlines(keepends=True)
    start_idx = -1
    base_indent = 0

    pattern = re.compile(r'^([ \t]*)(?:async\s+)?def\s+' + re.escape(func_name) + r'\b')
    for idx, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            start_idx = idx
            base_indent = len(m.group(1))
            break

    if start_idx == -1:
        return None

    # Find where function ends (next line with same or less indent that is not empty/comment)
    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        l = lines[idx]
        stripped = l.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(l) - len(l.lstrip())
        if indent <= base_indent:
            end_idx = idx
            break

    new_block = new_func_code.strip() + "\n"
    return "".join(lines[:start_idx]) + new_block + "".join(lines[end_idx:])

def extract_functions_from_code(code: str, language: str = "cpp") -> List[Tuple[str, str]]:
    """
    Extracts defined top-level functions and their complete implementations from code.
    Returns list of (function_name, full_function_code).
    """
    lang = (language or "cpp").lower()
    results: List[Tuple[str, str]] = []

    if lang in ("python", "py"):
        try:
            tree = ast.parse(code)
            lines = code.splitlines(keepends=True)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn_start = node.lineno - 1
                    fn_end = getattr(node, "end_lineno", len(lines))
                    fn_code = "".join(lines[fn_start:fn_end])
                    results.append((node.name, fn_code.strip()))
        except Exception:
            # Fallback regex for Python
            for m in re.finditer(r'^(?:async\s+)?def\s+([A-Za-z0-9_]+)\b', code, re.MULTILINE):
                results.append((m.group(1), code))
    else:
        # C++ / Java function extractor
        pattern = re.compile(
            r'^[ \t]*(?:template\s*<[^>]*>\s*)?(?:public|private|protected|static|inline|virtual|constexpr)?\s*[\w:<>\*&]+\s+([A-Za-z0-9_]+)\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*\{',
            re.MULTILINE
        )
        for m in pattern.finditer(code):
            func_name = m.group(1)
            brace_start = m.end() - 1
            brace_end = _find_brace_matching_block(code, brace_start)
            if brace_end != -1:
                func_code = code[m.start():brace_end + 1]
                results.append((func_name, func_code.strip()))

    return results

def reconstruct_full_code(original_code: str, fix_snippet: str, language: str = "cpp") -> str:
    """
    Reconstructs the 100% complete source code when the AI outputs a targeted patch,
    a single function, or code with placeholder comments.
    
    If the file is 5,000 lines and the AI only modified 1 function, this preserves
    all 4,990 untouched lines and returns the COMPLETE 5,000-line code.
    """
    if not fix_snippet or not fix_snippet.strip():
        return original_code
    if not original_code or not original_code.strip():
        return fix_snippet.strip()

    lang = (language or "cpp").lower()
    orig_lines = original_code.splitlines()
    fix_lines = fix_snippet.splitlines()

    # Case 1: If original code is small (< 150 lines), and fix_snippet is full code, return fix_snippet
    if len(orig_lines) < 150 and not has_placeholder(fix_snippet):
        if len(fix_lines) >= len(orig_lines) * 0.8:
            return fix_snippet.strip()

    # Case 2: If fix_snippet already has >= 95% of original lines and no placeholders, it's full code
    if len(fix_lines) >= len(orig_lines) * 0.95 and not has_placeholder(fix_snippet):
        return fix_snippet.strip()

    # Case 3: Targeted Function Splicing
    # Extract functions present in the fix_snippet
    cleaned_snippet = clean_placeholders(fix_snippet)
    extracted_funcs = extract_functions_from_code(cleaned_snippet, language=lang)

    reconstructed = original_code
    spliced_any = False

    for func_name, func_code in extracted_funcs:
        if lang in ("python", "py"):
            res = _splice_python_function(reconstructed, func_name, func_code)
        else:
            res = _splice_cpp_function(reconstructed, func_name, func_code)

        if res:
            reconstructed = res
            spliced_any = True

    if spliced_any:
        return reconstructed.strip()

    # Case 4: Missing include / import fix
    # If fix_snippet contains includes/imports not in original_code, prepend or append
    if lang in ("cpp", "c++", "c"):
        includes = re.findall(r'^[ \t]*#include\s*<[^>]+>', fix_snippet, re.MULTILINE)
        missing_includes = [inc for inc in includes if inc not in original_code]
        if missing_includes:
            return "\n".join(missing_includes) + "\n" + original_code

    if lang in ("python", "py"):
        imports = re.findall(r'^[ \t]*(?:import\s+[\w.]+|from\s+[\w.]+\s+import\s+[\w* ,]+)', fix_snippet, re.MULTILINE)
        missing_imports = [imp for imp in imports if imp not in original_code]
        if missing_imports:
            return "\n".join(missing_imports) + "\n" + original_code

    # Fallback: If fix_snippet has substantial lines (> 80% of original), use fix_snippet
    if len(fix_lines) >= len(orig_lines) * 0.8:
        return fix_snippet.strip()

    # Otherwise, return original_code if fix was a tiny fragment that couldn't be mapped
    return original_code
