"""Track background corpus ingest on container startup (Railway / Docker)."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Literal

IngestPhase = Literal["idle", "running", "succeeded", "failed"]

_lock = threading.Lock()
_phase: IngestPhase = "idle"
_started_at: str | None = None
_finished_at: str | None = None
_exit_code: int | None = None
_error_hint: str | None = None
_mode: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def mark_running(mode: str) -> bool:
    """Return False if ingest already started."""
    global _phase, _started_at, _finished_at, _exit_code, _error_hint, _mode
    with _lock:
        if _phase == "running":
            return False
        _phase = "running"
        _mode = mode
        _started_at = _now()
        _finished_at = None
        _exit_code = None
        _error_hint = None
        return True


def mark_finished(exit_code: int, *, stderr_tail: str = "") -> None:
    global _phase, _finished_at, _exit_code, _error_hint
    with _lock:
        _finished_at = _now()
        _exit_code = exit_code
        if exit_code == 0:
            _phase = "succeeded"
            _error_hint = None
        else:
            _phase = "failed"
            _error_hint = (stderr_tail or "Ingest subprocess failed").strip()[-500:]


def snapshot() -> dict[str, Any]:
    with _lock:
        return {
            "status": _phase,
            "mode": _mode,
            "started_at": _started_at,
            "finished_at": _finished_at,
            "exit_code": _exit_code,
            "error": _error_hint,
        }
