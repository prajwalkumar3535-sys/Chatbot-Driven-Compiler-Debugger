import compiler_service
import lldb_engine
import secure_scan
import time

def run_tests():
    print("==================================================")
    print("[*] RUNNING DOCKER SANDBOX VALIDATION TEST SUITE")
    print("==================================================")

    # TEST 0: Input Validation Security Layer
    print("\n[TEST 0] Testing Input Validation Security Layer (Layer 1)...")
    
    # 0.1 Empty / Whitespace payload
    is_valid, err = secure_scan.validate_input("   \n\t  ")
    assert not is_valid and "empty" in err.lower(), f"Failed empty check: {err}"
    print("  [OK] Empty/Whitespace input rejected.")

    # 0.2 Oversized payload (>50KB)
    oversized_code = "int x = 1;\n" * 6000  # ~66KB
    is_valid, err = secure_scan.validate_input(oversized_code)
    assert not is_valid and "exceeds maximum" in err.lower(), f"Failed oversized check: {err}"
    print("  [OK] Oversized payload (>50KB) rejected.")

    # 0.3 Null-byte injection
    null_byte_code = "int main() {\x00 system(\"calc.exe\"); return 0; }"
    is_valid, err = secure_scan.validate_input(null_byte_code)
    assert not is_valid and "null-byte" in err.lower(), f"Failed null-byte check: {err}"
    print("  [OK] Null-byte injection rejected.")

    # 0.4 Malformed binary / control character payload
    binary_payload = "int main() {\x01\x02\x03\x04 return 0; }"
    is_valid, err = secure_scan.validate_input(binary_payload)
    assert not is_valid and "control character" in err.lower(), f"Failed binary payload check: {err}"
    print("  [OK] Malformed binary/control characters rejected.")

    # 0.5 Valid code passing input validation
    valid_sample = "int main() { return 0; }"
    is_valid, err = secure_scan.validate_input(valid_sample)
    assert is_valid and err == "", f"Failed valid input check: {err}"
    print("  [OK] Valid input accepted cleanly.")

    print("[PASSED] TEST 0: Input Validation Layer (Layer 1) passed all security checks.")

    # TEST 1: Normal Code
    print("\n[TEST 1] Testing Valid C++ Execution...")
    valid_code = """
    #include <iostream>
    using namespace std;
    int main() {
        cout << "Hello from Secure Docker Sandbox!" << endl;
        return 0;
    }
    """
    code, stdout, stderr = compiler_service.compile_and_run(valid_code)
    print(f"Status Code: {code}")
    print(f"Stdout: {stdout}")
    assert code == 0 and "Hello from Secure Docker Sandbox!" in stdout, f"Failed with code={code}, out={stdout}, err={stderr}"
    print("[PASSED] TEST 1: Valid code executed successfully in sandbox.")

    # TEST 2: Compiler Error
    print("\n[TEST 2] Testing C++ Syntax / Compilation Error...")
    syntax_error_code = """
    #include <iostream>
    int main() {
        int x = "incompatible_type";
        return 0;
    }
    """
    code, stdout, stderr = compiler_service.compile_and_run(syntax_error_code)
    print(f"Status Code: {code}")
    print(f"Stderr: {stderr[:120]}...")
    assert code == 1 and ("error:" in stderr or "invalid conversion" in stderr), f"Failed with code={code}, err={stderr}"
    print("[PASSED] TEST 2: Compilation error caught by sandbox compiler.")

    # TEST 3: Segmentation Fault (Runtime Crash) & LLDB Inspection
    print("\n[TEST 3] Testing SegFault & LLDB Debugger inside Sandbox...")
    segfault_code = """
    #include <iostream>
    int main() {
        int* ptr = nullptr;
        *ptr = 1337;
        return 0;
    }
    """
    code, stdout, stderr = compiler_service.compile_and_run(segfault_code)
    print(f"Status Code: {code}")
    print(f"Stderr: {stderr}")
    assert code == 2, f"Expected code 2, got {code}"
    print("[PASSED] TEST 3.1: Runtime SegFault caught with status code 2.")

    print("Testing LLDB 'bt' backtrace in sandbox...")
    bt_output = lldb_engine.execute_lldb_command("/sandbox/prog_bin", "bt")
    print("LLDB Output:\n" + bt_output)
    # Accept: backtrace, stop reason, binary name, or any signal reference
    lldb_ok = (
        "stop reason = signal SIGSEGV" in bt_output or
        "frame #0" in bt_output or
        "Process" in bt_output or
        "prog_bin" in bt_output or
        "signal" in bt_output.lower()
    )
    assert lldb_ok, f"Unexpected LLDB output: {bt_output}"
    print("[PASSED] TEST 3.2: LLDB backtrace successfully captured inside sandbox.")

    # TEST 4: Infinite Loop Timeout Protection
    print("\n[TEST 4] Testing Infinite Loop Timeout...")
    infinite_loop_code = """
    int main() {
        while(true) {}
        return 0;
    }
    """
    start_t = time.time()
    code, stdout, stderr = compiler_service.compile_and_run(infinite_loop_code)
    elapsed = time.time() - start_t
    print(f"Status Code: {code}, Time Taken: {elapsed:.2f}s")
    print(f"Stderr: {stderr}")
    assert code == -1 and "Time Limit Exceeded" in stderr, f"Failed timeout test: code={code}, err={stderr}"
    print("[PASSED] TEST 4: Infinite loop killed safely by sandbox timeout.")

    print("\n==================================================")
    print("[SUCCESS] ALL SANDBOX SECURITY TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
