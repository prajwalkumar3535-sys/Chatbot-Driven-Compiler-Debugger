"""
routers/run.py - Code Execution Endpoint with Sandboxing, Layer 1 & 2 Guardrails, and Green Metrics
"""

import sys
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from compiler_service import compile_and_run
from secure_scan import run_security_guardrail, validate_input
from error_classifier import classify_error
from security_logger import log_security_event
from app.metrics import GreenTracker
from app.ast_generator import generate_ast_analysis

router = APIRouter(prefix="/api", tags=["execution"])

class RunRequest(BaseModel):
    language: str = Field(default="cpp", description="cpp | python | java")
    code: str = Field(..., description="Source code to execute")
    stdin: Optional[str] = Field(default="", description="Optional standard input")

class RunResponse(BaseModel):
    stdout: str
    stderr: str
    compile_output: str
    exit_code: int
    status: str  # "accepted" | "compile_error" | "runtime_error" | "time_limit_exceeded" | "security_blocked" | "system_error"
    time_ms: float
    memory_kb: int
    energy_wh: float
    carbon_g: float
    eco_score: str
    eco_label: str
    delta_time_ms: Optional[float] = None
    delta_energy_wh: Optional[float] = None
    error_category: Optional[str] = None
    error_strategy: Optional[str] = None
    ast: Optional[Dict[str, Any]] = None

@router.post("/ast")
def get_ast(req: RunRequest):
    """Generates structural Abstract Syntax Tree (AST) analysis for given code & language."""
    return generate_ast_analysis(req.code, language=req.language)

@router.post("/run", response_model=RunResponse)
def run_code(req: RunRequest):
    """
    Executes source code inside zero-trust Docker container sandbox (or host fallback)
    with hard memory limits, zero network access, and Green Sandbox environmental metrics.
    """
    lang = (req.language or "cpp").lower().strip()
    code = req.code or ""
    stdin_data = req.stdin or ""

    # Layer 1: Input Validation
    is_valid, val_err = validate_input(code, language=lang)
    if not is_valid:
        log_security_event("INPUT_VALIDATION_BLOCK", "HIGH", val_err, code, language=lang)
        return RunResponse(
            stdout="",
            stderr=f"⚠️ Input Validation Error: {val_err}",
            compile_output="",
            exit_code=400,
            status="security_blocked",
            time_ms=0.5,
            memory_kb=1024,
            energy_wh=0.000001,
            carbon_g=0.000001,
            eco_score="A+",
            eco_label="Validation Block"
        )

    # Layer 2: Pre-Scan Static Guardrails
    is_hard_blocked, block_msg, soft_warnings = run_security_guardrail(code, language=lang)
    if is_hard_blocked:
        log_security_event("STATIC_GUARDRAIL_BLOCK", "CRITICAL", block_msg, code, language=lang)
        return RunResponse(
            stdout="",
            stderr=f"🚫 SECURITY GUARDRAIL BLOCK: {block_msg}",
            compile_output="",
            exit_code=403,
            status="security_blocked",
            time_ms=1.2,
            memory_kb=2048,
            energy_wh=0.000005,
            carbon_g=0.000002,
            eco_score="A+",
            eco_label="Security Block"
        )

    # Begin Green Sandbox Tracking
    tracker = GreenTracker(project_name=f"{lang}_sandbox")
    tracker.start()

    # Execute in Sandbox
    return_code, stdout, stderr = compile_and_run(code, language=lang, stdin_data=stdin_data)

    # End Green Metrics Tracking
    metrics = tracker.stop()

    # Determine execution status and classification
    status = "accepted"
    category = None
    strategy = None

    if return_code == 0:
        status = "accepted"
    elif return_code == 1:
        status = "compile_error"
        category, strategy = classify_error(stderr, language=lang)
    elif return_code == 2:
        status = "runtime_error"
        category, strategy = classify_error(stderr, language=lang)
    elif "Time Limit Exceeded" in stderr:
        status = "time_limit_exceeded"
    else:
        status = "system_error"

    # Prepend soft warnings if present
    if soft_warnings and status == "accepted":
        warning_header = "⚠️ [Advisory Warnings]:\n" + "\n".join(f"- {w}" for w in soft_warnings) + "\n\n"
        stderr = warning_header + (stderr or "")

    # Generate AST Analysis
    ast_info = generate_ast_analysis(code, language=lang)

    return RunResponse(
        stdout=stdout or "",
        stderr=stderr or "",
        compile_output="",
        exit_code=return_code,
        status=status,
        time_ms=metrics["time_ms"],
        memory_kb=metrics["memory_kb"],
        energy_wh=metrics["energy_wh"],
        carbon_g=metrics["carbon_g"],
        eco_score=metrics["eco_score"],
        eco_label=metrics["eco_label"],
        delta_time_ms=metrics.get("delta_time_ms"),
        delta_energy_wh=metrics.get("delta_energy_wh"),
        error_category=category,
        error_strategy=strategy,
        ast=ast_info
    )
