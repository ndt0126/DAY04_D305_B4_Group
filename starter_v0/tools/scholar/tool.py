from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, err

_OPENALEX = "https://api.openalex.org/works"


def _contact() -> str:
    # OpenAlex asks callers to identify themselves; doing so gets you the faster
    # "polite pool". Falls back to the lab's generic UA when unset.
    return os.getenv("OPENALEX_MAILTO") or os.getenv("ARXIV_USER_AGENT") or "ai20k-day04-lab"


def _authors(work: dict[str, Any], cap: int = 3) -> str:
    names = [
        (entry.get("author") or {}).get("display_name")
        for entry in (work.get("authorships") or [])
    ]
    names = [name for name in names if name]
    if not names:
        return "Unknown"
    shown = ", ".join(names[:cap])
    return f"{shown} et al." if len(names) > cap else shown


def find_scholarly_works(
    query: str = "",
    min_year: int | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Answer one question: "which published work on this topic is most established?"

    Ranking is deliberately two-stage. Asking OpenAlex to sort by citation count
    directly discards its relevance ranking, which surfaces whatever mega-cited
    paper happens to share a word with the query (searching "retrieval augmented
    generation" that way returns the SciPy paper). Instead we let OpenAlex pick a
    topically relevant candidate pool, then sort that pool by citations locally.
    No API key required.
    """
    try:
        if not str(query).strip():
            raise ValueError("query must not be empty")
        limit = max(1, min(int(limit or 5), 25))
        # Commas, pipes and colons are OpenAlex filter separators.
        safe_query = re.sub(r"[,|:]", " ", query).strip()

        filters = [f"title_and_abstract.search:{safe_query}"]
        if min_year is not None:
            year = int(min_year)
            if not 1800 <= year <= 2100:
                raise ValueError(f"min_year looks wrong: {year}")
            filters.append(f"publication_year:>{year - 1}")

        # Over-fetch by relevance so the local citation sort has something to rank.
        pool_size = max(limit * 5, 25)
        params: dict[str, Any] = {
            "filter": ",".join(filters),
            "per-page": min(pool_size, 200),
            "mailto": _contact(),
        }

        response = requests.get(_OPENALEX, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        raw = data.get("results") or []

        if not raw:
            # Title/abstract matching is strict; fall back to the broader index.
            params.pop("filter")
            params["search"] = safe_query
            if min_year is not None:
                params["filter"] = f"publication_year:>{int(min_year) - 1}"
            response = requests.get(_OPENALEX, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            raw = data.get("results") or []

        works = []
        for work in raw:
            venue = ((work.get("primary_location") or {}).get("source") or {}).get("display_name")
            open_access = work.get("open_access") or {}
            doi = work.get("doi")
            works.append({
                "title": work.get("display_name") or work.get("title"),
                "authors": _authors(work),
                "year": work.get("publication_year"),
                "venue": venue,
                "cited_by_count": work.get("cited_by_count", 0),
                "doi": doi,
                "url": open_access.get("oa_url") or doi or work.get("id"),
                "is_open_access": bool(open_access.get("is_oa")),
            })

        # Stage two: rank the relevant pool by how established each work is.
        works.sort(key=lambda w: w["cited_by_count"] or 0, reverse=True)
        works = works[:limit]

        if not works:
            return {
                "tool": "find_scholarly_works",
                "query": query,
                "min_year": min_year,
                "works": [],
                "total_found": 0,
                "verdict": f"No published work found for {query!r}. Try broader keywords.",
            }

        top = works[0]
        verdict = (
            f"Most-cited work on {query!r}: {top['title']!r} "
            f"({top['year']}, {top['cited_by_count']:,} citations)"
        )

        return {
            "tool": "find_scholarly_works",
            "query": query,
            "min_year": min_year,
            # The conclusion first, the evidence after it.
            "verdict": verdict,
            "most_cited": top,
            "works": works,
            "total_found": (data.get("meta") or {}).get("count", len(works)),
        }
    except Exception as exc:
        return err("find_scholarly_works", exc)
