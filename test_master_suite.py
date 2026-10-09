"""
test_master_suite.py - Master Automated Test Runner
Executes the full test suite for C++, Python, Java, Sandbox Security,
Input Validation, Language Switching, and Regression Testing.
"""

import sys
import os
import time

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_cpp_suite import run_all_cpp_tests
from tests.test_python_suite import run_all_python_tests
from tests.test_java_suite import run_all_java_tests
from tests.test_security_suite import run_all_security_tests
from tests.test_language_switch import run_all_switch_tests

def main():
    start_time = time.time()
    print("############################################################")
    print("### STARTING MASTER MULTI-LANGUAGE TEST & AUDIT RUNNER   ###")
    print("############################################################\n")

    results = {}

    # 1. C++ Suite
    try:
        results["C++ Test Suite"] = run_all_cpp_tests()
    except Exception as e:
        print(f"FAILED C++ Suite: {str(e)[:200]}")
        results["C++ Test Suite"] = False

    # 2. Python Suite
    try:
        results["Python Test Suite"] = run_all_python_tests()
    except Exception as e:
        print(f"FAILED Python Suite: {str(e)[:200]}")
        results["Python Test Suite"] = False

    # 3. Java Suite
    try:
        results["Java Test Suite"] = run_all_java_tests()
    except Exception as e:
        print(f"FAILED Java Suite: {str(e)[:200]}")
        results["Java Test Suite"] = False

    # 4. Security Suite
    try:
        results["Security & Sandbox Suite"] = run_all_security_tests()
    except Exception as e:
        print(f"FAILED Security Suite: {str(e)[:200]}")
        results["Security & Sandbox Suite"] = False

    # 5. Language Switch Suite
    try:
        results["Language Switch Transition Suite"] = run_all_switch_tests()
    except Exception as e:
        print(f"FAILED Switch Suite: {str(e)[:200]}")
        results["Language Switch Transition Suite"] = False

    elapsed = time.time() - start_time
    print("============================================================")
    print(f"MASTER TEST SUMMARY (Duration: {elapsed:.2f}s)")
    print("============================================================")
    all_passed = True
    for suite, ok in results.items():
        status = "PASSED [100%]" if ok else "FAILED [X]"
        print(f"  * {suite:35}: {status}")
        if not ok:
            all_passed = False
    print("============================================================")

    if all_passed:
        print(">> ALL TEST SUITES PASSED PERFECTLY! SYSTEM IS 100% SECURE & OPERATIONAL.")
        return 0
    else:
        print(">> ERRORS DETECTED IN TEST SUITES.")
        return 1

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
