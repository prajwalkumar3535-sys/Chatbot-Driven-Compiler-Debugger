# Chatbot-Driven C++ Compiler Debugger
An Automated Program Repair (APR) teaching assistant designed to help college students securely diagnose and fix C++ compilation errors using localized AI.

## Proposed Architecture
Our architecture functions as a secure wrapper around the standard GCC compiler.
* **Frontend:** Streamlit-based web UI.
* **Security Pipeline:** 4-Layer Defense-in-Depth Architecture:
  1. **Layer 1 (Input Validation):** Validates payload size (<=50KB), line limits, rejects null-byte (`\0`) injections, and filters malformed binary/control characters before processing.
  2. **Layer 2 (Pre-Scan Guardrails):** AST and heuristic regex rules that hard-block dangerous OS calls (`system`, `popen`, `exec*`, `gets`, etc.) and raise soft advisories.
  3. **Layer 3 (Containerized Docker Sandbox):** Hardened Docker container (`cpp-sandbox`) enforcing `--network none`, `--memory 256m`, `--cpus 1.0`, `--pids-limit 32`, `--cap-drop ALL`, and timeout kill switches.
  4. **Layer 4 (Post-Scan & Logic Audit):** Post-execution AST fix validation, emissions logging (CodeCarbon), and audit trail logging.
* **Diagnostic Engine:** Heuristic classification module for raw GCC errors and autonomous LLDB backtrace inspector.
* **AI Core:** Localized Llama 3 Large Language Model (LLM via Ollama).

## Methodology / Pipeline
1. **Input Validation (Layer 1):** Checks payload bounds, null bytes, and character sanitization.
2. **Pre-Scan Guardrails (Layer 2):** Scans user input for forbidden OS command injections and buffer overflow exploits.
3. **Sandboxed Compilation & Execution (Layer 3):** Passes code to GCC and runs binaries inside a hardened, ephemeral Docker container (`--network none`, `--memory 256m`, `--pids-limit 32`, `--cap-drop ALL`).
4. **Agentic LLDB Debugging:** On runtime crashes (SegFault/Abort), boots an LLDB instance inside the sandbox to inspect stack frames and registers.
5. **Classification:** Intercepts compiler errors and classifies them using a rule-based engine.
6. **AI Generation:** LLM receives a constrained prompt with compiler / debugger logs to generate a pedagogical fix.
7. **Post-Scan Audit (Layer 4):** Validates the LLM's suggested code before presenting it to the user.

## Sandbox Setup
1. Change directory to this project folder:
   ```bash
   cd Chatbot-Driven-Compiler-Debugger
   ```
2. Build the Docker sandbox image:
   ```bash
   docker build -t cpp-sandbox -f Dockerfile.sandbox .
   ```
3. Run the validation test suite:
   ```bash
   python test_sandbox_suite.py
   ```
4. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

