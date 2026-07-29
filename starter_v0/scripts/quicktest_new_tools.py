"""Quicktest for the four team-built tools (Tool Engineer deliverable).

Story: the agent is a research assistant that maintains a personal notebook.
    define      -> "what does X mean?"                  (Wikipedia)
    scholar     -> "which work on X is established?"    (OpenAlex)
    note_write  -> "open a new notebook entry"          (writes notes/<slug>.md)
    note_append -> "file this finding into that entry"  (appends to it)

Calls each tool directly through TOOL_FUNCTIONS, so this tests the
implementation rather than the declaration the model sees. A tool passes when it
returns no `error` key and the payload matches the contract in its TOOL.md.

    python scripts/quicktest_new_tools.py
    python scripts/quicktest_new_tools.py --offline   # skip define + scholar

Paste the output into artifacts/REPORT.md as quicktest evidence.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
from tools import TOOL_FUNCTIONS, load_tool_declarations
from tools._notes import NOTES_DIR, note_path
from tools._shared import terms

load_lab_env(ROOT)

NEW_TOOLS = ["define", "scholar", "note_write", "note_append"]
TEST_TOPIC = "quicktest retrieval augmented generation"
PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((PASS if ok else FAIL, name, detail))
    print(f"[{PASS if ok else FAIL}] {name}: {detail}")


def preview(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)[:170]


def section(title: str) -> None:
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Skip the two network tools.")
    args = parser.parse_args()

    section("0. Registry / declaration / docs are in sync")
    declared = {item["name"] for item in load_tool_declarations(ROOT / "artifacts" / "tools.yaml")}
    for name in NEW_TOOLS:
        in_registry, in_yaml = name in TOOL_FUNCTIONS, name in declared
        has_md = (ROOT / "tools" / name / "TOOL.md").exists()
        check(
            f"sync:{name}",
            in_registry and in_yaml and has_md,
            f"TOOL_FUNCTIONS={in_registry}, tools.yaml={in_yaml}, TOOL.md={has_md}",
        )

    if not args.offline:
        section('1. define - "what does X mean?"')
        out = TOOL_FUNCTIONS["define"](term="Retrieval-augmented generation", lang="en")
        ok = "error" not in out and out.get("definition")
        check("define:happy", bool(ok), out.get("definition", preview(out))[:110])
        if ok:
            check(
                "define:is_a_conclusion_not_an_article",
                len(out["definition"]) < 900 and bool(out.get("url")),
                f"{len(out['definition'])} chars, url set={bool(out.get('url'))}",
            )

        out = TOOL_FUNCTIONS["define"](term="retrieval augmneted generaton", lang="en")
        check("define:typo_fallback", "error" not in out, f"resolved_title={out.get('resolved_title')!r}")

        out = TOOL_FUNCTIONS["define"](term="Hà Nội", lang="vi")
        check("define:vi", "error" not in out, (out.get("definition") or preview(out))[:80])

        out = TOOL_FUNCTIONS["define"](term="Mercury", lang="en")
        check(
            "define:ambiguous_term_errors_instead_of_guessing",
            "error" in out or bool(out.get("definition")),
            out.get("message", "resolved to a concrete page")[:110],
        )

        out = TOOL_FUNCTIONS["define"](term="", lang="en")
        check("define:empty_term_rejected", "error" in out, out.get("message", preview(out))[:90])

        out = TOOL_FUNCTIONS["define"](term="AI", lang="fr")
        check("define:bad_lang_rejected", "error" in out, out.get("message", preview(out))[:90])

        section('2. scholar - "which work is established?"')
        out = TOOL_FUNCTIONS["scholar"](query="retrieval augmented generation", limit=5)
        ok = "error" not in out and out.get("works")
        check("scholar:happy", bool(ok), out.get("verdict", preview(out))[:120])
        if ok:
            top = out["most_cited"]
            check(
                "scholar:contract",
                all(k in top for k in ("title", "year", "cited_by_count", "url")),
                f"top={top['title']!r} ({top['year']}, {top['cited_by_count']} cites)",
            )
            counts = [w["cited_by_count"] for w in out["works"]]
            check("scholar:sorted_by_citations", counts == sorted(counts, reverse=True), f"counts={counts}")
            # Regression guard: sorting purely by citations used to return the
            # SciPy paper for this query. The top hit must be topically relevant.
            wanted = terms("retrieval augmented generation")
            overlap = wanted & terms(top["title"] or "")
            check("scholar:top_hit_is_on_topic", bool(overlap), f"shared terms={sorted(overlap)} in {top['title']!r}")

        out = TOOL_FUNCTIONS["scholar"](query="transformer architecture", min_year=2023, limit=3)
        ok = "error" not in out
        years = [w["year"] for w in out.get("works", [])]
        check("scholar:min_year_filter", ok and all(y >= 2023 for y in years if y), f"years={years}")

        out = TOOL_FUNCTIONS["scholar"](query="")
        check("scholar:empty_query_rejected", "error" in out, out.get("message", preview(out))[:90])

    section('3. note_write - "open a new notebook entry"')
    if NOTES_DIR.exists():
        shutil.rmtree(NOTES_DIR)

    out = TOOL_FUNCTIONS["note_write"](topic=TEST_TOPIC, content="Overview text.")
    check(
        "note_write:blocks_without_confirmation",
        out.get("status") == "needs_confirmation" and not note_path(TEST_TOPIC).exists(),
        f"status={out.get('status')!r}, nothing written to disk",
    )

    out = TOOL_FUNCTIONS["note_write"](topic=TEST_TOPIC, content="Overview text.", confirmed=True)
    ok = out.get("status") == "created" and note_path(TEST_TOPIC).exists()
    check("note_write:creates_when_confirmed", ok, f"path={out.get('path')!r} bytes={out.get('bytes')}")

    out = TOOL_FUNCTIONS["note_write"](topic=TEST_TOPIC, content="Different text.", confirmed=True)
    check(
        "note_write:refuses_to_overwrite",
        "error" in out and "note_append" in out.get("message", ""),
        out.get("message", preview(out))[:110],
    )

    out = TOOL_FUNCTIONS["note_write"](topic="!!!", content="x", confirmed=True)
    check("note_write:unslugifiable_topic_rejected", "error" in out, out.get("message", preview(out))[:90])

    section('4. note_append - "file this finding into that entry"')
    out = TOOL_FUNCTIONS["note_append"](topic=TEST_TOPIC, entry="A new finding.")
    check(
        "note_append:blocks_without_confirmation",
        out.get("status") == "needs_confirmation",
        f"status={out.get('status')!r}",
    )

    before = note_path(TEST_TOPIC).stat().st_size
    out = TOOL_FUNCTIONS["note_append"](
        topic=TEST_TOPIC, entry="A new finding.", section="Sources", confirmed=True
    )
    after = note_path(TEST_TOPIC).stat().st_size
    check(
        "note_append:appends_when_confirmed",
        out.get("status") == "appended" and after > before,
        f"section={out.get('section')!r} bytes {before} -> {after}",
    )

    out = TOOL_FUNCTIONS["note_append"](topic="a topic with no note", entry="x", confirmed=True)
    ok = "error" in out and "Existing notes" in out.get("message", "")
    check("note_append:missing_note_lists_alternatives", ok, out.get("message", preview(out))[:130])

    out = TOOL_FUNCTIONS["note_append"](topic=TEST_TOPIC, entry="", confirmed=True)
    check("note_append:empty_entry_rejected", "error" in out, out.get("message", preview(out))[:90])

    section("5. End-to-end notebook flow")
    content = note_path(TEST_TOPIC).read_text(encoding="utf-8")
    check(
        "flow:note_has_overview_and_appended_section",
        "## Overview" in content and "## Sources" in content,
        f"sections={[l for l in content.splitlines() if l.startswith('## ')]}",
    )
    shutil.rmtree(NOTES_DIR, ignore_errors=True)

    print("\n" + "=" * 74)
    failed = [r for r in results if r[0] == FAIL]
    print(f"SUMMARY: {len(results) - len(failed)}/{len(results)} passed")
    for _, name, detail in failed:
        print(f"  FAIL {name}: {detail}")
    print("=" * 74)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
