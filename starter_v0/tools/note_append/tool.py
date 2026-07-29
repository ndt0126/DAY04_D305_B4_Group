from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tools._notes import existing_notes, note_path, rel, slugify
from tools._shared import err


def append_to_research_note(
    topic: str = "",
    entry: str = "",
    section: str = "",
    confirmed: bool = False,
) -> dict[str, Any]:
    """Answer one question: "file this new finding into the notebook entry I already have."

    Appends to `notes/<slug>.md`. Never creates a note - that is `note_write`'s
    job - so a missing note surfaces as an error listing what does exist.
    """
    if not confirmed:
        return {
            "tool": "append_to_research_note",
            "status": "needs_confirmation",
            "message": "Only modify the note after the user explicitly confirms.",
            "would_append": {
                "topic": topic,
                "path": rel(note_path(topic)) if slugify(topic) else None,
                "section": section or "Findings",
                "entry_chars": len(entry or ""),
            },
        }
    try:
        if not str(topic).strip() or not slugify(topic):
            raise ValueError("topic must not be empty and must contain letters or digits")
        if not str(entry).strip():
            raise ValueError("entry must not be empty")

        path = note_path(topic)
        if not path.exists():
            available = existing_notes()
            raise FileNotFoundError(
                f"No note exists for {topic!r} (expected {rel(path)}). "
                f"Existing notes: {available or 'none'}. "
                f"Use note_write to create it first, or ask the user which note they meant."
            )

        now = datetime.now(timezone.utc)
        heading = (section or "Findings").strip()
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"\n## {heading}\n\n_{now:%Y-%m-%d %H:%M} UTC_\n\n{entry}\n")

        return {
            "tool": "append_to_research_note",
            "status": "appended",
            "topic": topic,
            "note": path.stem,
            "path": rel(path),
            "section": heading,
            "bytes": path.stat().st_size,
        }
    except Exception as exc:
        return err("append_to_research_note", exc)
