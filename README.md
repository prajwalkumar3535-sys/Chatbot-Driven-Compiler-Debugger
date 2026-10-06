# Chatbot-Driven C++ Compiler Debugger
An Automated Program Repair (APR) teaching assistant designed to help college students securely diagnose and fix C++ compilation errors using localized AI.

## Proposed Architecture
Our architecture functions as a secure wrapper around the standard GCC compiler.
* **Frontend:** Streamlit-based web UI.
* **Execution Sandbox:** Containerized Docker sandbox (`cpp-sandbox`) enforcing zero network access, memory caps (256MB), CPU limits, and PID limits to isolate host system.
* **Diagnostic Engine:** Heuristic classification module for raw GCC errors and autonomous LLDB backtrace inspector.
* **AI Core:** Localized Llama 3 Large Language Model (LLM via Ollama).
* **Security Pipeline:** Bi-directional validation system (Pre-scan regex guardrails + Containerized Sandboxing + Post-scan audit).

## Methodology / Pipeline
1. **Ingestion & Pre-Scan:** Scans user input for malicious system calls.
2. **Sandboxed Compilation & Execution:** Passes code to GCC and runs binaries inside a hardened, ephemeral Docker container (`--network none`, `--memory 256m`, `--pids-limit 32`, `--cap-drop ALL`).
3. **Agentic LLDB Debugging:** On runtime crashes (SegFault/Abort), boots an LLDB instance inside the sandbox to inspect stack frames and registers.
4. **Classification:** Intercepts compiler errors and classifies them using a rule-based engine.
5. **AI Generation:** LLM receives a constrained prompt with compiler / debugger logs to generate a pedagogical fix.
6. **Post-Scan Audit:** Validates the LLM's suggested code before presenting it to the user.

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

