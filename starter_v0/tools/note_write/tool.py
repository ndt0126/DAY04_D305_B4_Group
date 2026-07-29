from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tools._notes import NOTES_DIR, existing_notes, note_path, rel, slugify
from tools._shared import err


def write_research_note(
    topic: str = "",
    content: str = "",
    confirmed: bool = False,
) -> dict[str, Any]:
    """Answer one question: "open a new notebook entry for this topic."

    Creates `notes/<slug>.md`. Refuses to clobber an existing note - adding to
    one is `note_append`'s job, not this tool's.
    """
    if not confirmed:
        return {
            "tool": "write_research_note",
            "status": "needs_confirmation",
            "message": "Only create the note after the user explicitly confirms.",
            "would_create": {
                "topic": topic,
                "path": rel(note_path(topic)) if slugify(topic) else None,
                "content_chars": len(content or ""),
            },
        }
    try:
        if not str(topic).strip() or not slugify(topic):
            raise ValueError("topic must not be empty and must contain letters or digits")
        if not str(content).strip():
            raise ValueError("content must not be empty")

        path = note_path(topic)
        if path.exists():
            raise FileExistsError(
                f"Note {rel(path)!r} already exists. Use note_append to add to it "
                f"instead of overwriting."
            )

        now = datetime.now(timezone.utc)
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# {topic}\n\n"
            f"_Created {now:%Y-%m-%d %H:%M} UTC_\n\n"
            f"## Overview\n\n{content}\n",
            encoding="utf-8",
        )
        return {
            "tool": "write_research_note",
            "status": "created",
            "topic": topic,
            "note": path.stem,
            "path": rel(path),
            "bytes": path.stat().st_size,
            "existing_notes": existing_notes(),
        }
    except Exception as exc:
        return err("write_research_note", exc)
