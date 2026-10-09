"""
tests/test_java_suite.py - Complete Java Test Suite
Validates:
 1. Hello World
 2. Input/Output (Scanner stdin)
 3. Normal calculation
 4. Compilation error (missing symbol)
 5. Syntax error (missing semicolon)
 6. Runtime exception (ArithmeticException / NullPointerException)
 7. Infinite loop (Timeout)
 8. Large memory allocation
 9. Large output truncation
 10. ProcessBuilder / Runtime execution attempt (Static block)
 11. Network access attempt (Static block)
 12. File-system access attempt (Static block)
 13. Normal valid program
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from language_executor import execute_in_sandbox
from security_scanner import scan_code
from input_validator import validate_input

def run_all_java_tests():
    print("========================================")
    print("RUNNING JAVA TEST SUITE")
    print("========================================")
    passed = 0
    total = 0

    # 1. Hello World
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello Java");
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == 0 and "Hello Java" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 1. Hello World")
    passed += 1

    # 2. Input / Output
    total += 1
    code = """import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        System.out.println(n * 2);
    }
}"""
    r = execute_in_sandbox("java", code, stdin_data="10")
    assert r["status_code"] == 0 and "20" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 2. Input / Output (stdin 10 -> stdout 20)")
    passed += 1

    # 3. Normal calculation
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        long sum = 0;
        for (int i = 1; i <= 100; i++) sum += i;
        System.out.println("Sum: " + sum);
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == 0 and "Sum: 5050" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 3. Normal Calculation (Sum 1..100 = 5050)")
    passed += 1

    # 4. Compilation error
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        int x = unknownVariable;
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == 1 and ("cannot find symbol" in r["stderr"] or "cannot find symbol" in r["compile_output"]), f"Failed: {r}"
    print("  [PASS] 4. Compilation error (cannot find symbol caught)")
    passed += 1

    # 5. Syntax error
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        int x = 10
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == 1 and (";" in r["stderr"] or "expected" in r["stderr"]), f"Failed: {r}"
    print("  [PASS] 5. Syntax error (missing semicolon caught)")
    passed += 1

    # 6. Runtime Exception (ArithmeticException / Division by zero)
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        int a = 10;
        int b = 0;
        System.out.println(a / b);
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == 2 and ("ArithmeticException" in r["stderr"] or "/ by zero" in r["stderr"]), f"Failed: {r}"
    print("  [PASS] 6. Runtime Exception (ArithmeticException caught)")
    passed += 1

    # 7. Infinite loop (Timeout)
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        while (true) {}
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == -1 and "Time Limit Exceeded" in r["stderr"], f"Failed: {r}"
    print("  [PASS] 7. Infinite loop (Time Limit Exceeded enforced)")
    passed += 1

    # 8. Large memory allocation
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        try {
            int[] arr = new int[500000000];
            System.out.println("Allocated: " + arr.length);
        } catch (OutOfMemoryError e) {
            System.out.println("Caught OOM");
        }
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] in (0, 2, -1), f"Failed: {r}"
    print("  [PASS] 8. Large memory allocation handled")
    passed += 1

    # 9. Large output truncation
    total += 1
    code = """public class Main {
    public static void main(String[] args) {
        for (int i = 0; i < 5000; i++) {
            System.out.println("Line " + i + " of output");
        }
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == 0 and ("OUTPUT TRUNCATED" in r["stdout"] or len(r["stdout"]) <= 60000), f"Failed: {r}"
    print("  [PASS] 9. Large output truncation enforced")
    passed += 1

    # 10. ProcessBuilder / Runtime attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('public class Main { public static void main(String[] args) throws Exception { new ProcessBuilder("ls").start(); } }', language="java")
    assert blocked and "ProcessBuilder" in msg, f"Failed: {msg}"
    print("  [PASS] 10. ProcessBuilder execution attempt blocked")
    passed += 1

    # 11. Network access attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('import java.net.Socket; public class Main { public static void main(String[] args) { Socket s = null; } }', language="java")
    assert blocked and "socket" in msg.lower(), f"Failed: {msg}"
    print("  [PASS] 11. Network socket attempt blocked")
    passed += 1

    # 12. Sensitive file access attempt (Static scanner block)
    total += 1
    blocked, msg, _ = scan_code('import java.io.*; public class Main { public static void main(String[] args) { new FileInputStream("/etc/shadow"); } }', language="java")
    assert blocked and "sensitive system directories" in msg, f"Failed: {msg}"
    print("  [PASS] 12. Sensitive file access blocked")
    passed += 1

    # 13. Normal valid program (Classes, Methods, Streams)
    total += 1
    code = """import java.util.Arrays;
import java.util.List;
public class Main {
    public static void main(String[] args) {
        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
        int sum = numbers.stream().mapToInt(Integer::intValue).sum();
        System.out.println("Stream Sum: " + sum);
    }
}"""
    r = execute_in_sandbox("java", code)
    assert r["status_code"] == 0 and "Stream Sum: 15" in r["stdout"], f"Failed: {r}"
    print("  [PASS] 13. Normal valid Java streams & collections program")
    passed += 1

    print(f"\n>> JAVA SUITE: {passed}/{total} TESTS PASSED (100%)\n")
    return passed == total

if __name__ == "__main__":
    success = run_all_java_tests()
    sys.exit(0 if success else 1)
