"""Fail-closed safety guard. Both flags must be present for live writes."""
import os

def is_dry_run() -> bool:
    return os.getenv("DRY_RUN", "true").strip().lower() != "false"

def require_write_approval(dry_run: bool = True) -> None:
    if dry_run:
        return
    if is_dry_run() or os.getenv("YOUTUBE_WRITE_APPROVAL", "").strip() != "I_APPROVE":
        raise PermissionError(
            "YouTube changes blocked: set DRY_RUN=false and "
            "YOUTUBE_WRITE_APPROVAL=I_APPROVE after reviewing a preview."
        )
