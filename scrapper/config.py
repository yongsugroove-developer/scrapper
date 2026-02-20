from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_RELATED_KEYWORDS = (
    "마곡",
    "SH",
    "서울주택도시공사",
    "분양",
    "공급",
    "청약",
    "공고",
    "입주자모집",
)


@dataclass(frozen=True)
class Settings:
    timezone: str
    keyword: str
    related_keywords: tuple[str, ...]
    max_items: int
    dedupe_days: int
    search_results_per_query: int
    pre_score_threshold: int
    final_score_threshold: int
    fetch_timeout_seconds: int
    openai_api_key: str
    openai_model: str
    openai_base_url: str
    recipient_emails: tuple[str, ...]
    sender_email: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_app_password: str
    db_path: Path


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be integer: {raw}") from exc
    if value < minimum:
        raise ValueError(f"Environment variable {name} must be >= {minimum}: {value}")
    return value


def _list_env(name: str, default_values: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default_values
    values = tuple(part.strip() for part in raw.split(",") if part.strip())
    return values if values else default_values


def _recipient_emails() -> tuple[str, ...]:
    raw_multi = os.getenv("RECIPIENT_EMAILS", "").strip()
    if raw_multi:
        values = tuple(part.strip() for part in raw_multi.split(",") if part.strip())
        if values:
            # Keep order, remove duplicates.
            return tuple(dict.fromkeys(values))
    return (_required_env("RECIPIENT_EMAIL"),)


def load_settings() -> Settings:
    load_dotenv()

    timezone = os.getenv("TIMEZONE", "Asia/Seoul").strip() or "Asia/Seoul"
    keyword = os.getenv("KEYWORD", "sh 공사 마곡 분양").strip() or "sh 공사 마곡 분양"
    related_keywords = _list_env("RELATED_KEYWORDS", DEFAULT_RELATED_KEYWORDS)

    max_items = _int_env("MAX_ITEMS", default=10, minimum=1)
    dedupe_days = _int_env("DEDUPE_DAYS", default=7, minimum=1)
    search_results_per_query = _int_env("SEARCH_RESULTS_PER_QUERY", default=20, minimum=5)
    pre_score_threshold = _int_env("PRE_SCORE_THRESHOLD", default=24, minimum=1)
    final_score_threshold = _int_env("FINAL_SCORE_THRESHOLD", default=36, minimum=1)
    fetch_timeout_seconds = _int_env("FETCH_TIMEOUT_SECONDS", default=15, minimum=3)

    openai_api_key = _required_env("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"
    openai_base_url = os.getenv("OPENAI_BASE_URL", "").strip()

    recipient_emails = _recipient_emails()
    smtp_username = _required_env("SMTP_USERNAME")
    smtp_app_password = _required_env("SMTP_APP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL", "").strip() or smtp_username
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip() or "smtp.gmail.com"
    smtp_port = _int_env("SMTP_PORT", default=587, minimum=1)

    db_raw = os.getenv("DB_PATH", "data/scrapper.db").strip() or "data/scrapper.db"
    db_path = Path(db_raw)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path

    return Settings(
        timezone=timezone,
        keyword=keyword,
        related_keywords=related_keywords,
        max_items=max_items,
        dedupe_days=dedupe_days,
        search_results_per_query=search_results_per_query,
        pre_score_threshold=pre_score_threshold,
        final_score_threshold=final_score_threshold,
        fetch_timeout_seconds=fetch_timeout_seconds,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_base_url=openai_base_url,
        recipient_emails=recipient_emails,
        sender_email=sender_email,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_app_password=smtp_app_password,
        db_path=db_path,
    )

