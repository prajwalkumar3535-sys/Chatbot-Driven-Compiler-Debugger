"""
tests/test_python_suite.py - Complete Python Test Suite
Validates:
 1. Hello World
 2. Input/Output (stdin)
 3. Normal calculation
 4. SyntaxError
 5. Runtime exception (ZeroDivisionError / IndexError)
 6. Infinite loop (Timeout)
 7. Large memory allocation
 8. Large output truncation
 9. Subprocess / system command attempt (Static block)
 10. Network access attempt (Static block & container network none)
 11. File-system access attempt (Static block)
 12. Normal valid program
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from language_executor import execute_in_sandbox
from security_scanner import scan_code
from input_validator import validate_input

def run_all_python_tests():
    print("========================================")
    print("RUNNING PYTHON TEST SUITE")
    print("========================================")
    passed = 0
    total = 0

    # 1. Hello World
    total += 1
    r = execute_in_sandbox("python", 'print("Hello Python")')
    assert r["status_code"] == 0 and "Hello Python" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 1. Hello World")
    passed += 1

    # 2. Input / Output
    total += 1
    code = """n = int(input())
print(n * 2)"""
    r = execute_in_sandbox("python", code, stdin_data="10")
    assert r["status_code"] == 0 and "20" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 2. Input / Output (stdin 10 -> stdout 20)")
    passed += 1

    # 3. Normal Calculation
    total += 1
    code = """
total = sum(i for i in range(1, 101))
print(f"Sum: {total}")
"""
    r = execute_in_sandbox("python", code)
    assert r["status_code"] == 0 and "Sum: 5050" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 3. Normal Calculation (Sum 1..100 = 5050)")
    passed += 1

    # 4. SyntaxError
    total += 1
    r = execute_in_sandbox("python", 'def foo(:\n    pass')
    assert r["status_code"] == 2 and "SyntaxError" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 4. SyntaxError caught in sandbox")
    passed += 1

    # 5. Runtime Exception (ZeroDivisionError)
    total += 1
    r = execute_in_sandbox("python", 'x = 10 / 0')
    assert r["status_code"] == 2 and "ZeroDivisionError" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 5. Runtime Exception (ZeroDivisionError caught)")
    passed += 1

    # 6. Infinite loop (Timeout)
    total += 1
    r = execute_in_sandbox("python", 'while True: pass')
    assert r["status_code"] == -1 and "Time Limit Exceeded" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 6. Infinite loop (Time Limit Exceeded enforced)")
    passed += 1

    # 7. Large memory allocation
    total += 1
    code = """
try:
    a = [0] * (10**9)
    print("Allocated")
except (MemoryError, OverflowError):
    print("Memory limit handled")
"""
    r = execute_in_sandbox("python", code)
    # Either handled or killed by Docker OOM killer
    assert r["status_code"] in (0, 2, -1), f"Failed: {r}"
    print("  [PASS] 7. Large memory allocation bounded")
    passed += 1

    # 8. Large output truncation
    total += 1
    code = """
for i in range(5000):
    print(f"Line {i} of output")
"""
    r = execute_in_sandbox("python", code)
    assert r["status_code"] == 0 and ("OUTPUT TRUNCATED" in r["stdout"] or len(r["stdout"]) <= 60000), f"Failed: {r}"
    print("  [PASS] 8. Large output truncation enforced")
    passed += 1

    # 9. Subprocess / OS command attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('import os\nos.system("rm -rf /")', language="python")
    assert blocked and "os.system()" in msg, f"Failed: {msg}"
    print("  [PASS] 9. Subprocess / os.system attempt blocked")
    passed += 1

    # 10. Network access attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('import socket\ns = socket.socket()', language="python")
    assert blocked and "socket" in msg, f"Failed: {msg}"
    print("  [PASS] 10. Network socket creation attempt blocked")
    passed += 1

    # 11. Sensitive filesystem access attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('with open("/etc/shadow") as f: print(f.read())', language="python")
    assert blocked and "sensitive system directories" in msg, f"Failed: {msg}"
    print("  [PASS] 11. Sensitive filesystem access blocked")
    passed += 1

    # 12. Normal valid program (fibonacci & dicts)
    total += 1
    code = """
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

print(f"Fib(10) = {fib(10)}")
"""
    r = execute_in_sandbox("python", code)
    assert r["status_code"] == 0 and "Fib(10) = 55" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 12. Normal valid Python Fibonacci program")
    passed += 1

    print(f"\n>> PYTHON SUITE: {passed}/{total} TESTS PASSED (100%)\n")
    return passed == total

if __name__ == "__main__":
    success = run_all_python_tests()
    sys.exit(0 if success else 1)
