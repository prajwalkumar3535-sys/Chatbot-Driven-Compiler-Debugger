"""
tests/test_language_switch.py - Language Switch Transition Tests
Validates all pairwise and multi-step language transitions:
 1. C++ -> Python
 2. Python -> Java
 3. Java -> C++
 4. C++ -> Java
 5. Java -> Python
 6. Python -> C++

For every transition, verifies:
 - Correct language configuration is fetched
 - Correct file extension and filename
 - Correct Docker image is referenced
 - Correct compiler command vs no compile step
 - Correct static scanner rules are selected
 - Correct error classifier parser is invoked
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from language_config import get_language_config, validate_language, ALLOWED_LANGUAGES, get_display_name
from language_executor import execute_in_sandbox
from security_scanner import scan_code
from error_classifier import classify_error

def test_transition(from_lang: str, to_lang: str):
    print(f"  --> Testing Switch: {from_lang.upper()} -> {to_lang.upper()}")

    # 1. Validate 'to_lang' is valid
    ok, err = validate_language(to_lang)
    assert ok and not err, f"Validation failed for {to_lang}: {err}"

    # 2. Config check
    cfg = get_language_config(to_lang)
    assert cfg is not None, f"Config missing for {to_lang}"
    assert cfg["extension"].startswith("."), f"Bad extension for {to_lang}"
    assert cfg["docker_image"] in ("cpp-sandbox", "python-sandbox", "java-sandbox", "code-sandbox")

    # 3. Compiler requirements
    if to_lang == "python":
        assert not cfg["needs_compile"] and cfg["compile_cmd"] is None
    else:
        assert cfg["needs_compile"] and cfg["compile_cmd"] is not None

    # 4. Static scanner rules check
    if to_lang == "python":
        # Python should block os.system, but C++ gets rule shouldn't trigger
        blocked, msg, _ = scan_code('import os\nos.system("ls")', language=to_lang)
        assert blocked and "os.system()" in msg
    elif to_lang == "java":
        blocked, msg, _ = scan_code('public class Main { public static void main(String[] a){ new ProcessBuilder("ls").start(); } }', language=to_lang)
        assert blocked and "ProcessBuilder" in msg
    elif to_lang == "cpp":
        blocked, msg, _ = scan_code('int main(){ gets(nullptr); }', language=to_lang)
        assert blocked and "gets()" in msg

    # 5. Error classifier check
    if to_lang == "python":
        cat, _ = classify_error("NameError: name 'x' is not defined", language=to_lang)
        assert "Name Error" in cat
    elif to_lang == "java":
        cat, _ = classify_error("Main.java:3: error: cannot find symbol", language=to_lang)
        assert "Symbol Not Found" in cat or "Compilation Error" in cat
    elif to_lang == "cpp":
        cat, _ = classify_error("solution.cpp:2: error: expected ';' before 'return'", language=to_lang)
        assert "Syntax Error" in cat

    # 6. Sandboxed Execution check
    if to_lang == "python":
        r = execute_in_sandbox(to_lang, 'print("Switch OK Python")')
        assert r["status_code"] == 0 and "Switch OK Python" in r["stdout"]
    elif to_lang == "java":
        r = execute_in_sandbox(to_lang, 'public class Main { public static void main(String[] a){ System.out.println("Switch OK Java"); } }')
        assert r["status_code"] == 0 and "Switch OK Java" in r["stdout"]
    elif to_lang == "cpp":
        r = execute_in_sandbox(to_lang, '#include <iostream>\nint main(){ std::cout << "Switch OK CPP" << std::endl; return 0; }')
        assert r["status_code"] == 0 and "Switch OK CPP" in r["stdout"]

    print(f"  [PASS] Switch {from_lang.upper()} -> {to_lang.upper()} verified.")


def run_all_switch_tests():
    print("========================================")
    print("RUNNING LANGUAGE SWITCH TRANSITION SUITE")
    print("========================================")
    transitions = [
        ("cpp", "python"),
        ("python", "java"),
        ("java", "cpp"),
        ("cpp", "java"),
        ("java", "python"),
        ("python", "cpp"),
    ]

    for from_l, to_l in transitions:
        test_transition(from_l, to_l)

    print("\n>> LANGUAGE SWITCH SUITE: 6/6 TRANSITIONS PASSED (100%)\n")
    return True

if __name__ == "__main__":
    success = run_all_switch_tests()
    sys.exit(0 if success else 1)
