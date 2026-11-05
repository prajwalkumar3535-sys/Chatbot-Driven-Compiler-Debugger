# Collaborative Multi-Agent Sandbox Compiler & Debugger Platform

A production-grade Automated Program Repair (APR) and cloud compiler platform styled after CodeChef and Programiz. Features isolated Docker sandboxing, high-precision Green Sandbox Metrics (energy & carbon tracking), and collaborative Multi-Agent intelligence powered by **Microsoft Phi-3**, **Alibaba Qwen**, and **Meta Llama 3** via Ollama.

---

## 🌟 Key Capabilities
* **Monaco Editor Core:** Full VS Code editor engine with syntax highlighting, auto-completion, font scaling, minimap toggle, and keyboard shortcuts (`Ctrl+Enter` to run).
* **Multi-Language Sandboxing:** Secure sandboxed compilation and execution for **Python**, **C++**, and **Java** with full `stdin` standard input support.
* **Multi-Model Council (Consensus APR):** Solves bugs simultaneously with Llama 3, Phi-3, and Qwen, streaming comparisons side-by-side with security-audited recommendations and one-click code patch application.
* **Four Specialized AI Agents:**
  - 🎓 **Tutor Mentor:** Explains root causes, invariants, and time/space complexity (Big-O).
  - 🔍 **Detective Agent:** Pinpoints exact failure locations, tracebacks, and underlying mechanisms.
  - 🛠️ **Repair Agent:** Generates clean, minimal, compile-ready bug fixes preserving original logic.
  - 🛡️ **Security Sentinel:** Audits code for vulnerabilities, unsafe functions, and CWE/OWASP risks.
* **Green Sandbox Metrics:** Measures run latency, memory consumption, energy consumed (Wh), and carbon footprint (g CO₂eq) alongside an Eco Score badge (`A+`, `A`, `B`, `C`).
* **13-Layer Defense-in-Depth:** Input validation, AST guardrails, memory limits, non-root isolated Docker containers, cgroup caps, output sanitization, and AI fix verification.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│               Frontend: React + Vite + Monaco          │
│  - 56px CodeChef-style Top Navbar with Live Status     │
│  - Resizable Monaco Editor + Stdin/Output + Chat       │
│  - Real-time SSE Token Streaming & Markdown Rendering  │
└───────────────────────────▲────────────────────────────┘
                            │ REST / SSE (port 8000)
┌───────────────────────────▼────────────────────────────┐
│                  Backend: FastAPI + Uvicorn            │
│  - POST /api/run (Docker Sandbox + MinGW/Host Fallback)│
│  - POST /api/chat/stream (SSE Multi-Agent & Council)   │
│  - GET /api/models, /api/languages, /api/health        │
└─────────────▲────────────────────────────▲─────────────┘
              │ Sub-ms socket probe        │ Execution
┌─────────────▼──────────────┐   ┌─────────▼─────────────┐
│    Ollama LLM Engine       │   │ Docker Container Pool │
│ - Microsoft Phi-3 Mini     │   │ - python-sandbox      │
│ - Alibaba Qwen 2.5 Coder   │   │ - cpp-sandbox         │
│ - Meta Llama 3             │   │ - java-sandbox        │
└────────────────────────────┘   └───────────────────────┘
```

---

## 🚀 Quick Start

### 1. One-Click Launcher (PowerShell)

In Windows PowerShell, run:
```powershell
.\start.ps1
```
This automatically boots:
- **Backend:** `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)
- **Frontend:** `http://localhost:5173`

### 2. Manual Startup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🤖 Ollama Setup & Supported Models

Ensure [Ollama](https://ollama.ai) is installed and running on your system:

```bash
# 1. Start Ollama service
ollama serve

# 2. Pull Microsoft Phi-3 (Diagnostic Logic)
ollama pull phi3:mini

# 3. Pull Alibaba Qwen 2.5 Coder (Repair & Synthesis)
ollama pull qwen2.5:coder

# 4. Pull Meta Llama 3 (Security Sentinel & Tutor)
ollama pull llama3.2:1b
ollama pull llama3
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/run` | `POST` | Compiles & runs code in Docker sandbox; returns stdout, stderr, exit code, time, memory, energy, and carbon metrics. |
| `/api/chat/stream` | `POST` | Server-Sent Events (SSE) streaming tokens for single agent or Multi-Model Council comparison. |
| `/api/health` | `GET` | Health status of Ollama (sub-millisecond socket check) and Docker engine. |
| `/api/models` | `GET` | Discovers installed Ollama models with capability tags and active presets. |
| `/api/languages` | `GET` | Supported languages (Python, C++, Java), extensions, starter templates, and sample bugs. |
| `/api/agents` | `GET` | Metadata, icons, default models, and system prompts for all four agents. |

---

## 🔒 13-Layer Defense-in-Depth Pipeline

1. `input_validator.py` -> **Layer 1 (Input Validation):** Malformed/oversized code, null-byte injection, binary/control characters.
2. `security_scanner.py` -> **Layer 2 (Static Security Scanner) & Layer 12 (AI Fix Verification):** Blocks dangerous functions (`system`, `popen`, `gets`, `strcpy`, format strings) and validates LLM repair suggestions.
3. `Dockerfile` -> **Layer 3 (Docker Isolation), Layer 6 (Read-Only FS), Layer 7 (Non-Root Execution UID 1000):** Minimal Alpine-based build.
4. `docker_executor.py` -> **Layer 3, 4, 8 (Docker Executor):** Enforces `--network none`, `--cap-drop ALL`, isolated container runner.
5. `resource_controller.py` -> **Layer 5 (Resource Limits) & Layer 9 (Process/PID Limits):** 256MB RAM, 1.0 CPU, max 32 PIDs.
6. `output_controller.py` -> **Layer 10 (Output Limits):** Caps stdout/stderr to 50KB / 1000 lines & strips ANSI bombs.
7. `timeout_controller.py` -> **Layer 11 (Execution Timeout):** Hard execution kill switches (5s run, 12s compile).
8. `security_logger.py` -> **Layer 13 (Audit & Security Logging):** Real-time incident logging to `security_events.csv` and `system_interactions.json`.

---

## 🧪 Testing

1. Backend test suite:
   ```bash
   python backend/test_api.py
   ```
2. Frontend build verification:
   ```bash
   cd frontend
   npm run build
   ```
3. Multi-Agent test suite:
   ```bash
   python tests/test_multiagent_platform.py
   ```
4. 13-Layer security suite:
   ```bash
   python test_all_security_layers.py
   ```
