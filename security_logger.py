"""
security_logger.py - Layer 13: Audit & Security Logging
Maintains persistent audit records of security violations, input validation blocks,
runtime crashes, and AI repair verification events.
"""

import os
import csv
import json
from datetime import datetime
from typing import Any

SECURITY_LOG_CSV = "security_events.csv"
AUDIT_LOG_JSON = "system_interactions.json"

def _ensure_csv_headers():
    """Initializes CSV audit file if not present."""
    if not os.path.exists(SECURITY_LOG_CSV):
        with open(SECURITY_LOG_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Event_Type", "Severity", "Details", "Code_Snippet"])


def log_security_event(event_type: str, severity: str, details: str, code_snippet: str = "N/A"):
    """
    Appends a security incident (e.g. INPUT_VALIDATION_BLOCK, GUARDRAIL_TRIGGER) to the security log.
    """
    _ensure_csv_headers()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clean multi-line snippets for CSV storage
    clean_snippet = code_snippet.replace("\n", "\\n") if code_snippet != "N/A" else "N/A"
    if len(clean_snippet) > 500:
        clean_snippet = clean_snippet[:500] + "...[TRUNCATED]"

    try:
        with open(SECURITY_LOG_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, event_type, severity, details, clean_snippet])
    except Exception as e:
        print(f"[SECURITY_LOGGER ERROR] Failed to write to CSV: {e}")


def log_interaction_event(
    user_prompt: str,
    llm_response: str,
    code_snippet: str = "N/A",
    error_category: str = "N/A",
    fixed_code: str = "N/A",
    security_flag: str = "SAFE"
):
    """
    Appends a conversation turn with full security audit metadata to JSON history.
    """
    log_entry: dict[str, Any] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error_category": error_category,
        "security_flag": security_flag,
        "code_snippet": code_snippet,
        "user_prompt": user_prompt,
        "llm_response": llm_response,
        "fixed_code": fixed_code
    }

    data: list[dict[str, Any]] = []
    if os.path.exists(AUDIT_LOG_JSON):
        try:
            with open(AUDIT_LOG_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []

    data.append(log_entry)
    try:
        with open(AUDIT_LOG_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[SECURITY_LOGGER ERROR] Failed to write to JSON: {e}")
