"""Shared helpers for the research-notebook tools (`note_write`, `note_append`).

Team-built (Tool Engineer). Kept separate from `_shared.py` so the starter file
stays untouched.

A note lives at `notes/<slug>.md`, where the slug is derived deterministically
from the topic. That determinism is the point: `note_append` can find the note
`note_write` created without the model having to remember a filename.
"""
from __future__ import annotations

import re
from pathlib import Path

from tools._shared import ROOT, fold_text

NOTES_DIR = ROOT / "notes"
MAX_SLUG = 60


def slugify(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", fold_text(topic or "")).strip("-")
    return slug[:MAX_SLUG].rstrip("-")


def note_path(topic: str) -> Path:
    return NOTES_DIR / f"{slugify(topic)}.md"


def existing_notes() -> list[str]:
    if not NOTES_DIR.exists():
        return []
    return sorted(path.stem for path in NOTES_DIR.glob("*.md"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")
