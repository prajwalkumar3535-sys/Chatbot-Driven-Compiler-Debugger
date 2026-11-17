# 🤖 ChatBot: Multi-Agent Sandbox Compiler & Automated Program Repair Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/Frontend-React_19_+_Vite-61DAFB.svg?style=flat-square&logo=react)](https://react.dev/)
[![Monaco Editor](https://img.shields.io/badge/Editor-Monaco_(VS_Code)-007ACC.svg?style=flat-square&logo=visual-studio-code)](https://microsoft.github.io/monaco-editor/)
[![Ollama](https://img.shields.io/badge/Local_AI-Ollama_(100%25_Offline)-black.svg?style=flat-square&logo=ollama)](https://ollama.ai/)
[![Docker](https://img.shields.io/badge/Sandbox-Docker_Isolated-2496ED.svg?style=flat-square&logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

An enterprise-grade, privacy-first **Automated Program Repair (APR) and Cloud Compiler Platform**. Features zero-trust container sandboxing, high-precision hardware-calibrated Green Carbon Metrics, multi-tab file management with direct local PC file/folder access, AST (Abstract Syntax Tree) fault detection, and collaborative local AI debugging powered by **Microsoft Phi-3**, **Alibaba Qwen**, and **Meta Llama 3** via Ollama.

---

## 📑 Table of Contents

- [🌟 Features & Capabilities](#-features--capabilities)
- [🏗️ System Architecture](#️-system-architecture)
- [⚡ Quick Start (Run in 2 Minutes)](#-quick-start-run-in-2-minutes)
  - [Prerequisites](#prerequisites)
  - [Option A: Single-Command Launch (Recommended)](#option-a-single-command-launch-recommended)
  - [Option B: Manual Step-by-Step Setup](#option-b-manual-step-by-step-setup)
- [🤖 Setting Up Local AI Models (Ollama)](#-setting-up-local-ai-models-ollama)
- [🌳 Abstract Syntax Tree (AST) Engine](#-abstract-syntax-tree-ast-engine)
- [🌱 Green Sandbox & Carbon Footprint Metrics](#-green-sandbox--carbon-footprint-metrics)
- [🛡️ 13-Layer Defense-in-Depth Security](#️-13-layer-defense-in-depth-security)
- [📡 API Reference](#-api-reference)
- [🧪 Running the Test Suite](#-running-the-test-suite)
- [🔧 Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 🌟 Features & Capabilities

### 💻 Multi-Tab Monaco Editor & Local PC Integration
* **Full VS Code Core:** Syntax highlighting, code folding, bracket matching, minimap toggle, font scaling (`11px` to `24px`), and `Ctrl+Enter` shortcut to compile and run.
* **Multi-Tab File System:** Create clean, blank new tabs with `+ Tab`, close tabs, switch between multiple source files (`.cpp`, `.py`, `.java`), and double-click any tab to rename it inline.
* **Open Files & Folders from PC:** Open local source files directly from your computer or load an entire folder into the built-in Folder Explorer sidebar.
* **Full Standard Input (`stdin`):** Interactive stdin console to pass custom test cases and multi-line competitive programming inputs.
* **Flawless Light & Dark Themes:** Instant one-click toggle between deep dark mode (`#0b0f17`) and clean white light mode (`#ffffff`) across Monaco, tab bars, side panels, and terminal outputs.
* **Boxed "Apply to Editor":** AI code fixes are presented in dark syntax-highlighted code blocks with a one-click **"Apply to Editor"** button that immediately injects verified code into the active tab.

### ⚡ Multi-Language Sandboxed Execution
* **Zero-Trust Docker Sandbox:** Non-root execution for **Python**, **C++ (GCC/Clang)**, and **Java (OpenJDK)** with strict resource caps (`256MB` RAM, `1.0` CPU, `--network none`).
* **Native Host Clang++ Fallback:** Automatic host-level compilation via Clang++/MinGW if the Docker daemon is temporarily offline.
* **Sub-Second Latency:** Instant compilation feedback with real-time stdout/stderr color separation and ANSI formatting.

### 🤖 Collaborative Multi-Agent AI & Multi-Model Council
* **100% Local & Offline AI:** Runs locally on your machine via Ollama — zero cloud API keys, zero token fees, complete privacy.
* **Four Specialized Agent Roles:**
  - 🎓 **Tutor Mentor:** Explains programming concepts, underlying language invariants, and Big-O time/space complexity.
  - 🔍 **Detective Agent:** Pinpoints exact failure locations, line numbers, and root compiler errors using AST hierarchy.
  - 🛠️ **Repair Agent:** Generates clean, minimal, compile-ready bug fixes preserving your original code style.
  - 🛡️ **Security Sentinel:** Scans for memory vulnerabilities, dangerous function calls, and OWASP/CWE violations.
* **Multi-Model Council (Consensus APR):** Concurrently queries **Meta Llama 3**, **Microsoft Phi-3**, and **Alibaba Qwen**, evaluates proposals side-by-side, and synthesizes consensus.
* **Concise & Direct Guidance:** Agents provide straight-to-the-point technical solutions without unnecessary conversational fluff.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Frontend: React 19 + Vite                       │
│  - Multi-Tab Monaco Editor (VS Code core)                              │
│  - Local PC File & Folder Access                                       │
│  - Flawless Light & Dark Theme Support                                 │
│  - Output Panel: Terminal • Input (stdin) • Syntax Tree • Carbon       │
│  - Multi-Agent AI Chat with Boxed "Apply to Editor" Patches            │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ REST API & Server-Sent Events (SSE)
┌───────────────────────────────────▼────────────────────────────────────┐
│                       Backend: FastAPI + Uvicorn                       │
│  - POST /api/run: Sandboxed Execution & Green Metrics Engine           │
│  - POST /api/chat/stream: SSE Multi-Agent & Multi-Model Council Stream │
│  - POST /api/ast: Abstract Syntax Tree Generation & Symbol Extraction  │
│  - GET /api/health, /api/languages, /api/models, /api/agents           │
└───────────────▲───────────────────────────────────────▲────────────────┘
                │ Dynamic Model Resolver                │ Container Execution
┌───────────────▼────────────────┐      ┌───────────────▼────────────────┐
│      Ollama Local LLMs         │      │      Docker Sandbox Pool       │
│ - Microsoft Phi-3 Mini (3.8B)  │      │ - python-sandbox               │
│ - Alibaba Qwen 2.5 Coder (1.5B)│      │ - cpp-sandbox (GCC/Clang++)    │
│ - Meta Llama 3 (1B / 8B)       │      │ - java-sandbox (OpenJDK)       │
└────────────────────────────────┘      └────────────────────────────────┘
```

---

## ⚡ Quick Start (Run in 2 Minutes)

### Prerequisites

Before starting, make sure you have installed:
1. **Python 3.10+** — [python.org](https://www.python.org/downloads/)
2. **Node.js 18+** & npm — [nodejs.org](https://nodejs.org/)
3. **Ollama** (for local AI) — [ollama.ai](https://ollama.ai/)
4. *(Optional)* **Docker Desktop** (for containerized sandboxing) — [docker.com](https://www.docker.com/)

---

### Option A: Single-Command Launch (Recommended)

On **Windows PowerShell**, simply run:

```powershell
.\start.ps1
```

This single command will:
1. Check dependencies and virtual environment.
2. Start the **FastAPI Backend** on `http://localhost:8000`.
3. Start the **Vite React Frontend** on `http://localhost:5173`.
4. Open the application directly in your browser.

---

### Option B: Manual Step-by-Step Setup

If you prefer starting services manually in separate terminals:

#### Terminal 1 — Backend (FastAPI):
```bash
# Navigate to project root
cd Chatbot-Driven-Compiler-Debugger

# Create and activate a Python virtual environment
python -m venv venv

# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
# source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Start FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs on: `http://localhost:8000` (Swagger docs at `/docs`)*

#### Terminal 2 — Frontend (React + Vite):
```bash
# Navigate to frontend folder
cd Chatbot-Driven-Compiler-Debugger/frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```
*Frontend runs on: `http://localhost:5173`*

---

## 🤖 Setting Up Local AI Models (Ollama)

To use the AI Detective, Tutor, Repair, and Security Sentinel offline:

1. **Start the Ollama daemon:**
   ```bash
   ollama serve
   ```

2. **Pull the lightweight specialized models:**
   ```bash
   # Alibaba Qwen 2.5 Coder (Fast code synthesis & bug repair)
   ollama pull qwen2.5-coder:1.5b

   # Microsoft Phi-3 Mini (High-density fault localization & reasoning)
   ollama pull phi3:mini

   # Meta Llama 3.2 (Fast security triage & audit)
   ollama pull llama3.2:1b
   ```

> 💡 **Auto-Model Fallback:** The backend automatically maps and routes to whatever model weights you have installed (e.g. `qwen2.5-coder:1.5b`, `qwen2.5:latest`, `phi3:mini`, `llama3`). You never have to worry about `404 Model Not Found` errors.

---

## 🌳 Abstract Syntax Tree (AST) Engine

ChatBot includes an integrated multi-language AST generator:
* **Python:** Standard AST parsing identifying function definitions, classes, loop scopes, symbol references, and pinpointing syntax error line/column carets.
* **C++:** Clang AST analysis dumping structural tokens, binary operators, memory pointers, and function call hierarchies.
* **AI Context Injection:** When a compiler or runtime error occurs, the parsed AST hierarchy is injected directly into the LLM prompt. This gives the local model immediate structural awareness, preventing hallucinations and drastically accelerating fix generation.
* **Syntax Tree Tab:** Inspect the generated AST hierarchy directly under the **Syntax Tree (AST)** tab in the output panel.

---

## 🌱 Green Sandbox & Carbon Footprint Metrics

Every program run is monitored by a hardware-calibrated energy accounting engine:
* **Latency:** Real-time monotonic wall-clock timing in milliseconds (`ms`).
* **Peak Memory:** Measured in kilobytes (`KB`) capped at 256MB.
* **Energy Consumption:** Calculated in micro-watt-hours (`Wh`) using hardware CPU TDP modeling.
* **Carbon Emissions:** Estimated in grams of CO₂eq (`g`) using regional grid emission factors (~475g CO₂/kWh).
* **Eco Score:** Dynamic algorithmic grading (`A+`, `A`, `B`, `C`, `F`) with run-to-run delta comparisons.
* **Dedicated Tab:** View all energy analytics under the **Carbon Metrics** tab.

---

## 🛡️ 13-Layer Defense-in-Depth Security

| Layer | Module | Defense Mechanism |
|---|---|---|
| **1** | `input_validator.py` | Input validation against null-bytes, control characters, and file-bomb payloads. |
| **2** | `security_scanner.py` | Regex-based static analysis blocking dangerous APIs (`system()`, `popen()`, `exec()`, `strcpy()`, `gets()`). |
| **3** | `docker_executor.py` | Isolated Docker execution in hardened Alpine containers. |
| **4** | `docker_executor.py` | Network isolation (`--network none`) preventing exfiltration and botnets. |
| **5** | `resource_controller.py` | Hard memory ceilings (`256MB`) preventing Out-Of-Memory host crashes. |
| **6** | `Dockerfile` | Read-only container root filesystem (`--read-only`). |
| **7** | `Dockerfile` | Non-root container execution (`UID 1000` / `appuser`). |
| **8** | `docker_executor.py` | Linux capability drops (`--cap-drop ALL`). |
| **9** | `resource_controller.py` | Process fork-bomb protection (`pids-limit 32`). |
| **10** | `output_controller.py` | Terminal output truncator (max 50KB / 1000 lines) & ANSI sanitizer. |
| **11** | `timeout_controller.py` | Hard kill switches (5s execution, 12s compilation timeout). |
| **12** | `fix_engine.py` | AI repair validation verifying proposed fixes against security rules before display. |
| **13** | `security_logger.py` | Tamper-evident audit trail logged to `security_events.csv` and `system_interactions.json`. |

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/run` | Execute code in sandbox with input (stdin), resource limits, and green metrics. |
| `POST` | `/api/chat/stream` | Real-time SSE token stream for single agent or Multi-Model Council. |
| `POST` | `/api/ast` | Parse code and generate AST structural analysis. |
| `GET` | `/api/health` | Real-time health status of Ollama engine and Docker sandbox pool. |
| `GET` | `/api/models` | List installed and supported Ollama model tags. |
| `GET` | `/api/languages` | Get supported languages (C++, Python, Java) and default templates. |
| `GET` | `/api/agents` | Get available AI agents, roles, and model configurations. |

Interactive API documentation and schema explorer are available at `http://localhost:8000/docs`.

---

## 🧪 Running the Test Suite

```bash
# 1. Test 13-Layer Security Pipeline
python test_all_security_layers.py

# 2. Test Multi-Agent Platform & Council
python test_master_suite.py

# 3. Test Docker Sandbox Suite
python test_sandbox_suite.py

# 4. Verify Frontend TypeScript & Production Build
cd frontend
npm run build
```

---

## 🔧 Troubleshooting & FAQ

<details>
<summary><b>1. "Ollama Offline" pill shows in the Navbar</b></summary>

Make sure the Ollama service is active. Run `ollama serve` in a terminal window. If Ollama is running on a custom port or remote host, set the `OLLAMA_URL` environment variable:
```bash
set OLLAMA_URL=http://localhost:11434
```
</details>

<details>
<summary><b>2. Docker is not installed or Docker daemon is stopped</b></summary>

The application features an automatic **Native Host Fallback**. If Docker is not running, C++ code compiles directly via Clang++/MinGW on your host machine, and Python code runs in a sandboxed host subprocess. To enable full container isolation, install and start [Docker Desktop](https://www.docker.com/).
</details>

<details>
<summary><b>3. Port 8000 or 5173 is already in use</b></summary>

You can specify alternative ports:
- **Backend:** `python -m uvicorn backend.app.main:app --port 8080`
- **Frontend:** `npm run dev -- --port 3000`
</details>

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
