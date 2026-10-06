# Chatbot-Driven C++ Compiler Debugger
An Automated Program Repair (APR) teaching assistant designed to help college students securely diagnose and fix C++ compilation errors using localized AI.

## Proposed Architecture
Our architecture functions as a secure wrapper around the standard GCC compiler.
* **Frontend:** Streamlit-based web UI.
* **Security Pipeline:** 13-Layer Defense-in-Depth Architecture across 8 Modular Components:
  1. `input_validator.py` -> **Layer 1 (Input Validation):** Malformed/oversized code, null-byte injection, binary/control characters.
  2. `security_scanner.py` -> **Layer 2 (Static Security Scanner) & Layer 12 (AI Fix Verification):** Blocks dangerous functions (`system`, `popen`, `gets`, `strcpy`, format strings) and validates LLM repair suggestions.
  3. `Dockerfile` -> **Layer 3 (Docker Isolation), Layer 6 (Read-Only FS), Layer 7 (Non-Root Execution UID 1000):** Minimal Alpine-based build.
  4. `docker_executor.py` -> **Layer 3, 4, 8 (Docker Executor):** Enforces `--network none`, `--cap-drop ALL`, isolated container runner.
  5. `resource_controller.py` -> **Layer 5 (Resource Limits) & Layer 9 (Process/PID Limits):** 256MB RAM, 1.0 CPU, max 32 PIDs.
  6. `output_controller.py` -> **Layer 10 (Output Limits):** Caps stdout/stderr to 50KB / 1000 lines & strips ANSI bombs.
  7. `timeout_controller.py` -> **Layer 11 (Execution Timeout):** Hard execution kill switches (5s run, 12s compile).
  8. `security_logger.py` -> **Layer 13 (Audit & Security Logging):** Real-time incident logging to `security_events.csv` and `system_interactions.json`.

## Methodology / Pipeline
1. **Input Validation (Layer 1):** `input_validator.py` checks bounds and character sanitization.
2. **Pre-Scan Guardrails (Layer 2):** `security_scanner.py` scans for forbidden OS injection and memory exploits.
3. **Sandboxed Compilation & Execution (Layers 3–9):** Ephemeral non-root Docker container with drop capabilities, cgroup resource caps, zero network access.
4. **Agentic LLDB Debugging:** On runtime crashes (SegFault/Abort), boots an LLDB session in container to inspect registers and stack frames.
5. **Output & Timeout Enforcement (Layers 10–11):** `output_controller.py` and `timeout_controller.py` cap volume and terminate runaway loops.
6. **AI Fix Verification (Layer 12):** `security_scanner.py` scans LLM-generated code blocks before presenting to user.
7. **Security & Audit Logging (Layer 13):** `security_logger.py` logs events with timestamps and incident severity.

## Sandbox Setup & Testing
1. Change directory to this project folder:
   ```bash
   cd Chatbot-Driven-Compiler-Debugger
   ```
2. Build the Docker sandbox image:
   ```bash
   docker build -t cpp-sandbox -f Dockerfile .
   ```
3. Run the complete 13-layer security test suite:
   ```bash
   python test_all_security_layers.py
   ```
4. Run the end-to-end sandbox validation suite:
   ```bash
   python test_sandbox_suite.py
   ```
5. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

