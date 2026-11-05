"""
main.py - FastAPI Application Entrypoint
Exposes REST endpoints for Sandboxed Execution, Multi-Agent Chat Streaming, and System Metadata.
"""

import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend root and project root are in sys.path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

for path in [APP_DIR, BACKEND_DIR, PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from app.routers import run, chat, models

app = FastAPI(
    title="Multi-Agent Sandbox Compiler & Debugger API",
    description="High-performance backend for Sandboxed Code Execution, Green Metrics, and Multi-Agent APR",
    version="2.0.0"
)

# Enable CORS for frontend Vite development and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(run.router)
app.include_router(chat.router)
app.include_router(models.router)

@app.get("/")
async def root():
    return {
        "app": "Multi-Agent Sandbox Compiler & Debugger API",
        "status": "online",
        "version": "2.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

