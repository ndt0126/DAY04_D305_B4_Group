from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

_LANGS = {"en", "vi"}
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _user_agent() -> str:
    # Wikipedia rejects requests that do not identify themselves.
    return os.getenv("ARXIV_USER_AGENT") or "AI20k-Day04-Research-Agent/1.0 (educational lab)"


def _search_titles(term: str, lang: str, headers: dict[str, str]) -> tuple[str | None, str | None]:
    """Return (best title, spelling suggestion) for a term."""
    response = requests.get(
        f"https://{lang}.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": term,
            "srlimit": 1,
            "srinfo": "suggestion",
            "format": "json",
        },
        headers=headers,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json().get("query", {})
    hits = payload.get("search") or []
    suggestion = (payload.get("searchinfo") or {}).get("suggestion")
    return (hits[0].get("title") if hits else None), suggestion


def _resolve_title(term: str, lang: str, headers: dict[str, str]) -> str | None:
    title, suggestion = _search_titles(term, lang, headers)
    if title:
        return title
    # Heavy misspellings return no hits but do return a "did you mean" suggestion.
    if suggestion:
        corrected, _ = _search_titles(suggestion, lang, headers)
        return corrected
    return None


def define_concept(term: str = "", lang: str = "en", max_sentences: int = 2) -> dict[str, Any]:
    """Answer one question: "what does this term mean?"

    Returns a short, note-ready definition string - not an article, not a list
    of search results.
    """
    try:
        if not str(term).strip():
            raise ValueError("term must not be empty")
        if lang not in _LANGS:
            raise ValueError(f"lang must be one of {sorted(_LANGS)}, got {lang!r}")
        sentences = max(1, min(int(max_sentences or 2), 5))

        headers = {"User-Agent": _user_agent(), "Accept": "application/json"}

        def summary_for(title: str) -> requests.Response:
            return requests.get(
                f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}",
                headers=headers,
                timeout=TIMEOUT,
            )

        resolved = term
        response = summary_for(term)
        if response.status_code == 404:
            found = _resolve_title(term, lang, headers)
            if not found:
                raise LookupError(f"No encyclopedia entry found for {term!r} in {lang!r}")
            resolved = found
            response = summary_for(found)
        response.raise_for_status()
        data = response.json()

        if data.get("type") == "disambiguation":
            raise LookupError(
                f"{resolved!r} is ambiguous; ask the user which specific meaning they want"
            )

        extract = (data.get("extract") or "").strip()
        if not extract:
            raise LookupError(f"Entry {resolved!r} has no summary text")
        definition = " ".join(_SENTENCE_END.split(extract)[:sentences]).strip()

        return {
            "tool": "define_concept",
            "term": term,
            "lang": lang,
            "resolved_title": data.get("title") or resolved,
            # The conclusion: one short paragraph ready to paste into a note.
            "definition": definition,
            "short_description": data.get("description"),
            "url": (data.get("content_urls") or {}).get("desktop", {}).get("page") or "",
            "source": f"{lang}.wikipedia.org",
        }
    except Exception as exc:
        return err("define_concept", exc)
