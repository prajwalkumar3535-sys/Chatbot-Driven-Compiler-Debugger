"""
ast_generator.py - Multi-Language Abstract Syntax Tree (AST) Generator & Structural Analyzer
Extracts clean, hierarchical syntax trees, symbol scopes, control flow branch points,
and pinpoint syntax diagnostics for Python, C++, and Java.
Supplies structured AST context to LLM agents for faster and high-precision fault detection.
"""

import ast
import os
import re
import shutil
import subprocess
import tempfile
from typing import Dict, Any, List, Optional

CLANG_PATH = r"C:\Program Files\LLVM\bin\clang++.exe"
if not os.path.exists(CLANG_PATH):
    CLANG_PATH = shutil.which("clang++") or shutil.which("clang") or ""


# =====================================================================
# 1. PYTHON AST PARSER & TREE BUILDER
# =====================================================================

def _analyze_python_ast(code: str) -> Dict[str, Any]:
    """Parses Python source code into an AST and extracts a readable tree and symbols."""
    try:
        root = ast.parse(code)
    except SyntaxError as e:
        # High-precision syntax failure pointer
        line_no = e.lineno or 1
        col_offset = e.offset or 1
        err_line = e.text.rstrip() if e.text else ""
        pointer = " " * (col_offset - 1) + "^-- Syntax error detected here"

        err_detail = {
            "line": line_no,
            "column": col_offset,
            "message": e.msg,
            "snippet": f"Line {line_no}: {err_line}\n        {pointer}"
        }

        tree_lines = [
            f"❌ SYNTAX PARSE FAILED at Line {line_no}, Col {col_offset}: {e.msg}",
            f"   Offending code: {err_line}",
            f"   {pointer}",
            "",
            "Partial tokens parsed before termination:"
        ]

        return {
            "syntax_valid": False,
            "syntax_error": err_detail,
            "tree_text": "\n".join(tree_lines),
            "node_count": 0,
            "symbols": {"functions": [], "classes": [], "imports": [], "calls": []},
            "control_flow": {"branches": 0, "loops": 0, "try_blocks": 0},
            "summary": f"SyntaxError at line {line_no}: {e.msg}"
        }

    # Successful AST Parse
    tree_lines: List[str] = []
    functions: List[Dict[str, Any]] = []
    classes: List[Dict[str, Any]] = []
    imports: List[str] = []
    calls: List[Dict[str, Any]] = []
    node_count = 0
    branch_count = 0
    loop_count = 0
    try_count = 0

    def format_node(node: ast.AST, depth: int = 0) -> None:
        nonlocal node_count, branch_count, loop_count, try_count
        node_count += 1
        indent = "  " * depth

        if isinstance(node, ast.Module):
            tree_lines.append("Module (Root)")
            for child in ast.iter_child_nodes(node):
                format_node(child, depth + 1)

        elif isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            ret = f" -> {ast.unparse(node.returns)}" if getattr(node, "returns", None) else ""
            line = getattr(node, "lineno", "?")
            end_line = getattr(node, "end_lineno", line)
            tree_lines.append(f"{indent}├─ def {node.name}({', '.join(args)}){ret} [Lines {line}-{end_line}]")
            functions.append({"name": node.name, "args": args, "line": line, "end_line": end_line})
            for child in ast.iter_child_nodes(node):
                format_node(child, depth + 1)

        elif isinstance(node, ast.AsyncFunctionDef):
            args = [a.arg for a in node.args.args]
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ async def {node.name}({', '.join(args)}) [Line {line}]")
            functions.append({"name": node.name, "args": args, "line": line})
            for child in ast.iter_child_nodes(node):
                format_node(child, depth + 1)

        elif isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases]
            line = getattr(node, "lineno", "?")
            base_str = f"({', '.join(bases)})" if bases else ""
            tree_lines.append(f"{indent}├─ class {node.name}{base_str} [Line {line}]")
            classes.append({"name": node.name, "bases": bases, "line": line})
            for child in ast.iter_child_nodes(node):
                format_node(child, depth + 1)

        elif isinstance(node, ast.If):
            branch_count += 1
            test_str = ast.unparse(node.test)
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ if {test_str} [Line {line}]")
            for child in node.body:
                format_node(child, depth + 1)
            if node.orelse:
                tree_lines.append(f"{indent}│  else [Line {getattr(node.orelse[0], 'lineno', '?')}]")
                for child in node.orelse:
                    format_node(child, depth + 1)

        elif isinstance(node, (ast.For, ast.AsyncFor)):
            loop_count += 1
            target = ast.unparse(node.target)
            iter_str = ast.unparse(node.iter)
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ for {target} in {iter_str} [Line {line}]")
            for child in node.body:
                format_node(child, depth + 1)

        elif isinstance(node, ast.While):
            loop_count += 1
            test_str = ast.unparse(node.test)
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ while {test_str} [Line {line}]")
            for child in node.body:
                format_node(child, depth + 1)

        elif isinstance(node, ast.Try):
            try_count += 1
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ try [Line {line}]")
            for child in node.body:
                format_node(child, depth + 1)
            for handler in node.handlers:
                exc = ast.unparse(handler.type) if handler.type else "Exception"
                name = f" as {handler.name}" if handler.name else ""
                tree_lines.append(f"{indent}│  except {exc}{name} [Line {getattr(handler, 'lineno', '?')}]")
                for child in handler.body:
                    format_node(child, depth + 1)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                tree_lines.append(f"{indent}├─ import {alias.name} [Line {getattr(node, 'lineno', '?')}]")

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = [a.name for a in node.names]
            imp_str = f"from {mod} import {', '.join(names)}"
            imports.append(imp_str)
            tree_lines.append(f"{indent}├─ {imp_str} [Line {getattr(node, 'lineno', '?')}]")

        elif isinstance(node, ast.Assign):
            targets = [ast.unparse(t) for t in node.targets]
            val = ast.unparse(node.value)
            line = getattr(node, "lineno", "?")
            if len(val) > 35:
                val = val[:32] + "..."
            tree_lines.append(f"{indent}├─ assign: {', '.join(targets)} = {val} [Line {line}]")

        elif isinstance(node, ast.AnnAssign):
            target = ast.unparse(node.target)
            ann = ast.unparse(node.annotation)
            val = f" = {ast.unparse(node.value)}" if node.value else ""
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ assign: {target}: {ann}{val} [Line {line}]")

        elif isinstance(node, ast.Call):
            func_name = ast.unparse(node.func)
            line = getattr(node, "lineno", "?")
            calls.append({"name": func_name, "line": line})
            # Only list top-level or significant calls in tree to avoid clutter
            if depth <= 3:
                args_summary = f"({len(node.args)} args)"
                tree_lines.append(f"{indent}├─ call: {func_name}{args_summary} [Line {line}]")

        elif isinstance(node, ast.Return):
            val = ast.unparse(node.value) if node.value else "None"
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ return {val} [Line {line}]")

        elif isinstance(node, ast.Raise):
            exc = ast.unparse(node.exc) if node.exc else "reraise"
            line = getattr(node, "lineno", "?")
            tree_lines.append(f"{indent}├─ raise {exc} [Line {line}]")

        elif isinstance(node, ast.Expr):
            # Recurse into expression value (like Call)
            format_node(node.value, depth)

        else:
            # Recurse other blocks
            for child in ast.iter_child_nodes(node):
                if depth < 5:
                    format_node(child, depth + 1)

    format_node(root, depth=0)

    # Cap tree text length to ~60 lines for prompt token efficiency
    if len(tree_lines) > 60:
        clipped_count = len(tree_lines) - 60
        tree_lines = tree_lines[:60] + [f"  ... [clipped {clipped_count} deeper AST nodes]"]

    return {
        "syntax_valid": True,
        "syntax_error": None,
        "tree_text": "\n".join(tree_lines),
        "node_count": node_count,
        "symbols": {
            "functions": [f["name"] for f in functions],
            "classes": [c["name"] for c in classes],
            "imports": imports,
            "calls": list(set(c["name"] for c in calls))
        },
        "control_flow": {
            "branches": branch_count,
            "loops": loop_count,
            "try_blocks": try_count
        },
        "summary": f"Valid Python AST: {len(functions)} functions, {len(classes)} classes, {branch_count} branches, {loop_count} loops."
    }


# =====================================================================
# 2. C++ AST PARSER & TREE BUILDER (CLANG + STRUCTURAL FALLBACK)
# =====================================================================

def _analyze_cpp_ast(code: str) -> Dict[str, Any]:
    """
    Parses C++ code into an AST using Clang++ AST dump if available,
    falling back to a robust lexical grammar parser.
    """
    clang_tree_lines: List[str] = []
    syntax_error = None
    syntax_valid = True

    # Try Clang++ AST dump first
    if CLANG_PATH and os.path.exists(CLANG_PATH):
        try:
            with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            # Include MinGW headers if available for standard C++ headers
            cmd = [
                CLANG_PATH,
                "-fsyntax-only",
                "-Xclang", "-ast-dump",
                "--target=i686-pc-windows-gnu",
                "-IC:\\MinGW\\lib\\gcc\\mingw32\\6.3.0\\include\\c++",
                "-IC:\\MinGW\\lib\\gcc\\mingw32\\6.3.0\\include\\c++\\mingw32",
                "-IC:\\MinGW\\include",
                tmp_path
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            if proc.returncode == 0 and proc.stdout:
                # Parse Clang AST dump lines, filtering out system header noise
                raw_lines = proc.stdout.splitlines()
                user_lines = []
                for line in raw_lines:
                    # Ignore internal windows/CRT decls
                    if any(ignored in line for ignored in ("__int128", "_GUID", "__NSConstantString", "type_info", "__builtin_va_list", "__size_t")):
                        continue
                    if any(kw in line for kw in ("FunctionDecl", "CXXRecordDecl", "VarDecl", "CallExpr", "BinaryOperator", "ReturnStmt", "ForStmt", "WhileStmt", "IfStmt", "CompoundStmt")):
                        cleaned = re.sub(r"0x[0-9a-fA-F]+", "", line).strip()
                        cleaned = re.sub(r"<<invalid sloc>>|<invalid sloc>", "", cleaned).strip()
                        cleaned = re.sub(r"<[^>]+>", "", cleaned).strip()
                        user_lines.append(cleaned)
                if user_lines:
                    clang_tree_lines = user_lines[:50]
            elif proc.returncode != 0:
                err_text = proc.stderr or ""
                # Only treat as syntax error if not simply an unconfigured header path error
                if "fatal error: '" not in err_text:
                    syntax_valid = False
                    first_err = err_text.splitlines()[0] if err_text else "Syntax violation in C++ source"
                    syntax_error = {
                        "line": 1,
                        "column": 1,
                        "message": first_err,
                        "snippet": "\n".join(err_text.splitlines()[:4])
                    }
        except Exception:
            pass

    # Extract high-level structural AST (Functions, Classes, Loops, Pointers, Calls)
    func_pattern = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_:<>*&\s]+?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]*)\)\s*\{', re.MULTILINE)
    class_pattern = re.compile(r'^\s*(class|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE)
    include_pattern = re.compile(r'#include\s+[<"]([^>"]+)[>"]')
    call_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
    unsafe_mem_pattern = re.compile(r'\b(malloc|free|new|delete|strcpy|gets|strcat|system|popen)\b')

    lines = code.splitlines()
    tree_lines = ["TranslationUnit (C++ AST)"]
    functions = []
    classes = []
    includes = include_pattern.findall(code)
    unsafe_ops = []
    branch_count = 0
    loop_count = 0

    for inc in includes:
        tree_lines.append(f"  ├─ #include <{inc}>")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Class / Struct
        cm = class_pattern.search(line)
        if cm and not stripped.endswith(";"):
            c_name = cm.group(2)
            classes.append(c_name)
            tree_lines.append(f"  ├─ {cm.group(1)} {c_name} [Line {i}]")

        # Function Definition
        fm = func_pattern.search(line)
        if fm:
            ret_type = fm.group(1).strip()
            name = fm.group(2).strip()
            params = fm.group(3).strip()
            if name not in ("if", "for", "while", "switch", "catch"):
                functions.append(name)
                tree_lines.append(f"  ├─ FunctionDecl '{name}' ({params}) -> {ret_type} [Line {i}]")

        # Control Flow
        if re.search(r'\bif\s*\(', stripped):
            branch_count += 1
            tree_lines.append(f"  │  ├─ IfStmt [Line {i}]")
        elif re.search(r'\b(for|while)\s*\(', stripped):
            loop_count += 1
            loop_kind = "ForStmt" if "for" in stripped else "WhileStmt"
            tree_lines.append(f"  │  ├─ {loop_kind} [Line {i}]")
        elif re.search(r'\breturn\b', stripped):
            tree_lines.append(f"  │  ├─ ReturnStmt [Line {i}]")

        # Unsafe operations
        for op in unsafe_mem_pattern.findall(stripped):
            unsafe_ops.append(f"{op} (line {i})")

    # If Clang AST dump was captured, append summary
    if clang_tree_lines:
        tree_lines.append("  │")
        tree_lines.append("  └─ [Clang LLVM Concrete AST Excerpt]:")
        for cl in clang_tree_lines[:15]:
            tree_lines.append(f"     {cl}")

    return {
        "syntax_valid": syntax_valid,
        "syntax_error": syntax_error,
        "tree_text": "\n".join(tree_lines[:50]),
        "node_count": len(functions) + len(classes) + branch_count + loop_count,
        "symbols": {
            "functions": functions,
            "classes": classes,
            "imports": includes,
            "unsafe_ops": list(set(unsafe_ops))
        },
        "control_flow": {
            "branches": branch_count,
            "loops": loop_count,
            "try_blocks": len(re.findall(r'\btry\s*\{', code))
        },
        "summary": f"C++ AST: {len(functions)} functions, {len(classes)} classes/structs, {branch_count} branches, {loop_count} loops."
    }


# =====================================================================
# 3. JAVA AST PARSER & TREE BUILDER
# =====================================================================

def _analyze_java_ast(code: str) -> Dict[str, Any]:
    """Parses Java source code into high-level AST class and method structures."""
    class_pattern = re.compile(r'\b(?:public|protected|private)?\s*(?:static\s+)?class\s+([A-Za-z0-9_]+)')
    method_pattern = re.compile(r'\b(?:public|protected|private)\s+(?:static\s+)?([A-Za-z0-9_<>[\]]+)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*\{')
    import_pattern = re.compile(r'import\s+([A-Za-z0-9_.]+);')

    classes = class_pattern.findall(code)
    imports = import_pattern.findall(code)
    lines = code.splitlines()

    tree_lines = ["CompilationUnit (Java AST)"]
    for imp in imports:
        tree_lines.append(f"  ├─ import {imp}")

    functions = []
    branch_count = 0
    loop_count = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        cm = class_pattern.search(line)
        if cm:
            tree_lines.append(f"  ├─ class {cm.group(1)} [Line {i}]")

        mm = method_pattern.search(line)
        if mm:
            ret, name, params = mm.groups()
            functions.append(name)
            tree_lines.append(f"  │  ├─ MethodDecl {name}({params}) -> {ret} [Line {i}]")

        if re.search(r'\bif\s*\(', stripped):
            branch_count += 1
            tree_lines.append(f"  │  │  ├─ IfStmt [Line {i}]")
        elif re.search(r'\b(for|while)\s*\(', stripped):
            loop_count += 1
            tree_lines.append(f"  │  │  ├─ LoopStmt [Line {i}]")

    return {
        "syntax_valid": True,
        "syntax_error": None,
        "tree_text": "\n".join(tree_lines[:45]),
        "node_count": len(functions) + len(classes) + branch_count + loop_count,
        "symbols": {
            "functions": functions,
            "classes": classes,
            "imports": imports
        },
        "control_flow": {
            "branches": branch_count,
            "loops": loop_count,
            "try_blocks": len(re.findall(r'\btry\s*\{', code))
        },
        "summary": f"Java AST: {len(classes)} classes, {len(functions)} methods, {branch_count} branches."
    }


# =====================================================================
# 4. UNIFIED ENTRY POINT & LLM PROMPT BLOCK GENERATOR
# =====================================================================

def generate_ast_analysis(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Unified entry point to generate AST analysis for Python, C++, or Java.
    Returns structured data dictionary and a formatted 'ast_prompt_block'
    specifically formatted for injection into LLM multiagent prompts.
    """
    lang = (language or "python").lower()

    if lang in ("python", "py"):
        analysis = _analyze_python_ast(code)
    elif lang in ("cpp", "c++", "c"):
        analysis = _analyze_cpp_ast(code)
    elif lang in ("java",):
        analysis = _analyze_java_ast(code)
    else:
        analysis = _analyze_python_ast(code)

    analysis["language"] = lang

    # Build optimized Markdown prompt block for LLMs
    syntax_status = "VALID SYNTAX" if analysis.get("syntax_valid") else "SYNTAX ERROR DETECTED"
    symbols = analysis.get("symbols", {})
    ctrl = analysis.get("control_flow", {})

    prompt_lines = [
        "--- ABSTRACT SYNTAX TREE (AST) & STRUCTURAL CONTEXT ---",
        f"Language Parser Status: {syntax_status}",
        f"Functions Defined: {', '.join(symbols.get('functions', [])) or 'None'}",
        f"Classes Defined: {', '.join(symbols.get('classes', [])) or 'None'}",
        f"Control Flow: {ctrl.get('branches', 0)} branch points, {ctrl.get('loops', 0)} loops, {ctrl.get('try_blocks', 0)} try blocks",
    ]

    if not analysis.get("syntax_valid") and analysis.get("syntax_error"):
        err = analysis["syntax_error"]
        prompt_lines.append(f"⚠️ PARSE FAILURE: Line {err.get('line')}, Col {err.get('column')}: {err.get('message')}")
        if err.get("snippet"):
            prompt_lines.append(f"Failure Point:\n{err['snippet']}")

    prompt_lines.append("\nSyntax Hierarchy Tree:")
    prompt_lines.append(analysis.get("tree_text", ""))
    prompt_lines.append("-------------------------------------------------------")

    analysis["ast_prompt_block"] = "\n".join(prompt_lines)
    return analysis
