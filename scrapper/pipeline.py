from __future__ import annotations

from datetime import datetime
import logging
from collections import Counter
from zoneinfo import ZoneInfo

from openai import OpenAI

from scrapper.config import Settings
from scrapper.emailer import send_digest_email
from scrapper.models import RunReport, ScoredArticle, SearchResult, SummarizedArticle
from scrapper.ranking import canonicalize_url, is_similar_title, score_relevance
from scrapper.search import build_queries, search_web
from scrapper.storage import init_db, load_recent_sent, save_sent_articles
from scrapper.summarizer import summarize_article
from scrapper.text_extract import extract_article_text

logger = logging.getLogger(__name__)


def _collect_candidates(settings: Settings) -> tuple[int, int, list[ScoredArticle]]:
    queries = build_queries(settings.keyword, settings.related_keywords)
    raw_results = search_web(queries, settings.search_results_per_query)

    by_url: dict[str, SearchResult] = {}
    for result in raw_results:
        url = canonicalize_url(result.url)
        if url and url not in by_url:
            by_url[url] = result

    pre_ranked: list[tuple[int, str, SearchResult]] = []
    for canonical_url, result in by_url.items():
        score = score_relevance(
            settings.keyword,
            settings.related_keywords,
            result.title,
            result.snippet,
            "",
        )
        if score >= settings.pre_score_threshold:
            pre_ranked.append((score, canonical_url, result))

    pre_ranked.sort(key=lambda item: item[0], reverse=True)
    fetch_limit = max(settings.max_items * 5, settings.max_items + 10)
    pre_ranked = pre_ranked[:fetch_limit]

    sent_urls, sent_titles = load_recent_sent(settings.db_path, settings.dedupe_days)
    selected_titles: list[str] = list(sent_titles)
    selected: list[ScoredArticle] = []

    for _, canonical_url, result in pre_ranked:
        if canonical_url in sent_urls:
            continue
        if is_similar_title(result.title, selected_titles):
            continue

        extracted = extract_article_text(result.url, settings.fetch_timeout_seconds)
        final_score = score_relevance(
            settings.keyword,
            settings.related_keywords,
            result.title,
            result.snippet,
            extracted.text,
        )
        if final_score < settings.final_score_threshold:
            continue

        selected.append(
            ScoredArticle(
                search_result=result,
                canonical_url=canonical_url,
                extracted_text=extracted.text,
                extraction_method=extracted.method,
                score=final_score,
                published_at=extracted.published_at or result.published_at,
            )
        )
        selected_titles.append(result.title)

    selected.sort(key=lambda article: article.score, reverse=True)
    return len(raw_results), len(pre_ranked), selected[: settings.max_items]


def run_daily_pipeline(settings: Settings, dry_run: bool = False) -> RunReport:
    run_at = datetime.now(ZoneInfo(settings.timezone))
    init_db(settings.db_path)

    searched_count, candidates_count, selected = _collect_candidates(settings)

    summarized: list[SummarizedArticle] = []
    summary_success_count = 0
    summary_failed_count = 0
    summary_failed_urls: list[str] = []
    summary_failed_reason_counter: Counter[str] = Counter()
    if selected:
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        client = OpenAI(**client_kwargs)
        for article in selected:
            summary_result = summarize_article(client, settings.openai_model, settings.keyword, article)
            if summary_result.success:
                summary_success_count += 1
            else:
                summary_failed_count += 1
                summary_failed_urls.append(article.canonical_url)
                summary_failed_reason_counter[summary_result.reason] += 1
            summarized.append(
                SummarizedArticle(
                    title=article.search_result.title,
                    url=article.canonical_url,
                    score=article.score,
                    summary=summary_result.text,
                    published_at=article.published_at,
                )
            )

    sent_email = False
    if not dry_run:
        send_digest_email(settings, run_at, summarized)
        save_sent_articles(settings.db_path, summarized)
        sent_email = True

    summary_success_rate = (
        summary_success_count / len(summarized) if summarized else 0.0
    )
    if summary_failed_count > 0:
        logger.warning(
            (
                "Summary quality check | failed=%s success=%s rate=%.2f "
                "failed_reasons=%s failed_urls=%s"
            ),
            summary_failed_count,
            summary_success_count,
            summary_success_rate,
            dict(summary_failed_reason_counter),
            summary_failed_urls[:5],
        )

    return RunReport(
        run_at=run_at,
        searched_count=searched_count,
        candidates_count=candidates_count,
        selected_count=len(selected),
        summarized_count=len(summarized),
        summary_success_count=summary_success_count,
        summary_failed_count=summary_failed_count,
        summary_success_rate=summary_success_rate,
        summary_failed_urls=tuple(summary_failed_urls),
        summary_failed_reason_counts=tuple(summary_failed_reason_counter.items()),
        sent_email=sent_email,
        dry_run=dry_run,
    )
