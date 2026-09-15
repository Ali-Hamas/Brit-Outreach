"""Voice Cadence Service for Brit Outreach System & Hermes Agent.

Provides Hermes Agent with direct programmatic access to:
1. Identify prospects emailed >= 48 hours ago who have not replied.
2. Push them into the Voice Agent cold calling queue referencing info@ascentraconsulting.co.uk.
3. Sync booked meetings and call outcomes back into the CRM pipeline.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

VOICE_AGENT_DIR = Path(r"M:\Voice Agent")
VOICE_AGENT_PYTHON = VOICE_AGENT_DIR / ".venv" / "Scripts" / "python.exe"


def run_cadence_sync(cadence_hours: float = 48.0, dry_run: bool = False) -> Dict[str, Any]:
    """Triggers the 48-hour cadence sync between Brit Outreach System and Voice Agent."""
    cmd = [
        str(VOICE_AGENT_PYTHON if VOICE_AGENT_PYTHON.exists() else sys.executable),
        "-m",
        "app.voice_cadence_bridge",
        "--hours",
        str(cadence_hours),
    ]
    if dry_run:
        cmd.append("--dry-run")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(VOICE_AGENT_DIR),
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "success": True,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.CalledProcessError as e:
        logger.error("Failed to run voice cadence bridge: %s\n%s", e.stdout, e.stderr)
        return {
            "success": False,
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr,
        }


def sync_call_outcomes() -> Dict[str, Any]:
    """Syncs call outcomes (meeting_booked, qualified, not_interested) back to Brit Outreach CRM."""
    cmd = [
        str(VOICE_AGENT_PYTHON if VOICE_AGENT_PYTHON.exists() else sys.executable),
        "-m",
        "app.voice_cadence_bridge",
        "--sync-outcomes",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(VOICE_AGENT_DIR),
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "success": True,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_cadence_sync()
    print("Cadence sync result:", result)
