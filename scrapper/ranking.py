from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from rapidfuzz import fuzz

TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def canonicalize_url(raw_url: str) -> str:
    try:
        parsed = urlparse(raw_url)
        if not parsed.scheme or not parsed.netloc:
            return raw_url.strip()
        cleaned_query = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS
        ]
        normalized = parsed._replace(query=urlencode(cleaned_query, doseq=True), fragment="")
        return urlunparse(normalized)
    except ValueError:
        return raw_url.strip()


def score_relevance(
    core_keyword: str,
    related_keywords: tuple[str, ...],
    title: str,
    snippet: str,
    body: str,
) -> int:
    merged = " ".join((title, snippet, body)).lower()
    score = 0

    core = core_keyword.lower().strip()
    if core and core in merged:
        score += 100

    core_tokens = tuple(token for token in core.split() if token)
    token_hits = sum(1 for token in core_tokens if token in merged)
    score += token_hits * 15

    for keyword in related_keywords:
        lowered = keyword.lower().strip()
        if lowered and lowered in merged:
            score += 8

    for term in ("분양", "청약", "공고", "입주자모집"):
        if term in merged:
            score += 6

    return score


def is_similar_title(title: str, existing_titles: list[str], threshold: int = 90) -> bool:
    source = title.strip().lower()
    if not source:
        return False
    for current in existing_titles:
        target = current.strip().lower()
        if not target:
            continue
        if fuzz.ratio(source, target) >= threshold:
            return True
    return False

