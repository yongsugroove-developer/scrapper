from __future__ import annotations

from collections import OrderedDict
from typing import Iterable

from duckduckgo_search import DDGS

from scrapper.models import SearchResult


def build_queries(core_keyword: str, related_keywords: tuple[str, ...]) -> list[str]:
    ordered = OrderedDict[str, None]()
    ordered[core_keyword.strip()] = None
    for keyword in related_keywords:
        candidate = keyword.strip()
        if not candidate:
            continue
        ordered[f"{core_keyword} {candidate}"] = None
    return [query for query in ordered.keys() if query]


def search_web(queries: Iterable[str], max_results_per_query: int) -> list[SearchResult]:
    results: list[SearchResult] = []

    with DDGS() as ddgs:
        for query in queries:
            try:
                rows = ddgs.text(
                    query,
                    region="kr-kr",
                    safesearch="off",
                    max_results=max_results_per_query,
                )
            except Exception:
                continue

            for row in rows:
                title = str(row.get("title", "")).strip()
                url = str(row.get("href", "")).strip()
                snippet = str(row.get("body", "")).strip()
                if not title or not url:
                    continue
                results.append(
                    SearchResult(
                        query=query,
                        title=title,
                        url=url,
                        snippet=snippet,
                        source="duckduckgo",
                    )
                )

    return results

