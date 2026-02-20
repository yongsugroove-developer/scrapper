from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SearchResult:
    query: str
    title: str
    url: str
    snippet: str
    source: str
    published_at: str = ""


@dataclass(frozen=True)
class ExtractedContent:
    text: str
    method: str
    published_at: str = ""


@dataclass(frozen=True)
class ScoredArticle:
    search_result: SearchResult
    canonical_url: str
    extracted_text: str
    extraction_method: str
    score: int
    published_at: str = ""


@dataclass(frozen=True)
class SummarizedArticle:
    title: str
    url: str
    score: int
    summary: str
    published_at: str = ""


@dataclass(frozen=True)
class SummaryResult:
    text: str
    success: bool
    reason: str


@dataclass(frozen=True)
class RunReport:
    run_at: datetime
    searched_count: int
    candidates_count: int
    selected_count: int
    summarized_count: int
    summary_success_count: int
    summary_failed_count: int
    summary_success_rate: float
    summary_failed_urls: tuple[str, ...]
    summary_failed_reason_counts: tuple[tuple[str, int], ...]
    sent_email: bool
    dry_run: bool

