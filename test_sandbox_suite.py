import compiler_service
import lldb_engine
import time

def run_tests():
    print("==================================================")
    print("[*] RUNNING DOCKER SANDBOX VALIDATION TEST SUITE")
    print("==================================================")

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
    bt_output = lldb_engine.execute_lldb_command("/sandbox/prog", "bt")
    print("LLDB Output:\n" + bt_output)
    assert "stop reason = signal SIGSEGV" in bt_output or "frame #0" in bt_output, f"Unexpected LLDB output: {bt_output}"
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
