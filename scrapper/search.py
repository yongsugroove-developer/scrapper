from __future__ import annotations

from collections import OrderedDict
import logging
from typing import Iterable
import warnings

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from scrapper.models import SearchResult

logger = logging.getLogger(__name__)
_DDGS_RENAME_WARNING = "This package (`duckduckgo_search`) has been renamed to `ddgs`"


def build_queries(core_keyword: str, related_keywords: tuple[str, ...]) -> list[str]:
    ordered = OrderedDict[str, None]()
    ordered[core_keyword.strip()] = None
    for keyword in related_keywords:
        candidate = keyword.strip()
        if not candidate:
            continue
        ordered[f"{core_keyword} {candidate}"] = None
    return [query for query in ordered.keys() if query]


def _create_ddgs() -> DDGS:
    original_warn = warnings.warn

    def _filtered_warn(message, *args, **kwargs):  # type: ignore[no-untyped-def]
        if _DDGS_RENAME_WARNING in str(message):
            return
        return original_warn(message, *args, **kwargs)

    warnings.warn = _filtered_warn  # type: ignore[assignment]
    try:
        return DDGS()
    finally:
        warnings.warn = original_warn  # type: ignore[assignment]


def _search_bing(query: str, max_results: int) -> list[SearchResult]:
    if max_results <= 0:
        return []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    results: list[SearchResult] = []
    seen_urls: set[str] = set()

    # Bing uses 1-based offsets: 1, 11, 21, ...
    for first in range(1, max_results + 1, 10):
        if len(results) >= max_results:
            break

        params = {"q": query, "setlang": "ko", "first": first}
        before_count = len(results)
        try:
            response = requests.get(
                "https://www.bing.com/search",
                params=params,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Search failed | query=%s page_first=%s error=%s", query, first, exc)
            break

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("li.b_algo")
        if not items:
            break

        for item in items:
            link = item.select_one("h2 a")
            if link is None:
                continue

            title = link.get_text(" ", strip=True)
            url = (link.get("href") or "").strip()
            snippet_el = item.select_one("div.b_caption p") or item.select_one("p")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            date_el = item.select_one("span.news_dt") or item.select_one(".news_dt")
            published_at = date_el.get_text(" ", strip=True) if date_el else ""

            if not title or not url or url in seen_urls:
                continue

            seen_urls.add(url)
            results.append(
                SearchResult(
                    query=query,
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="bing",
                    published_at=published_at,
                )
            )
            if len(results) >= max_results:
                break

        # No useful new rows -> stop paging.
        if len(results) == before_count:
            break

    return results


def search_web(queries: Iterable[str], max_results_per_query: int) -> list[SearchResult]:
    results: list[SearchResult] = []
    try:
        ddgs = _create_ddgs()
        with ddgs:
            for query in queries:
                rows: list[SearchResult] = []
                ddgs_rows = ddgs.text(
                    query,
                    region="kr-kr",
                    safesearch="off",
                    max_results=max_results_per_query,
                )
                for row in ddgs_rows:
                    title = str(row.get("title", "")).strip()
                    url = str(row.get("href", "")).strip()
                    snippet = str(row.get("body", "")).strip()
                    if not title or not url:
                        continue
                    rows.append(
                        SearchResult(
                            query=query,
                            title=title,
                            url=url,
                            snippet=snippet,
                            source="duckduckgo",
                            published_at=str(row.get("date", "")).strip(),
                        )
                    )
                if not rows:
                    rows = _search_bing(query, max_results_per_query)
                results.extend(rows)
            return results
    except Exception as exc:
        logger.warning("DDGS session failed | fallback to requests | error=%s", exc)

    for query in queries:
        rows = _search_bing(query, max_results_per_query)
        results.extend(rows)

    return results

