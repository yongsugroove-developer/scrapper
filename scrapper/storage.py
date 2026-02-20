from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scrapper.models import SummarizedArticle


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_articles (
                url TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                sent_at_utc TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sent_articles_sent_at
            ON sent_articles(sent_at_utc)
            """
        )
        conn.commit()


def load_recent_sent(db_path: Path, window_days: int) -> tuple[set[str], list[str]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    cutoff_iso = cutoff.isoformat()

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT url, title
            FROM sent_articles
            WHERE sent_at_utc >= ?
            """,
            (cutoff_iso,),
        ).fetchall()

    urls = {str(row[0]) for row in rows if row[0]}
    titles = [str(row[1]) for row in rows if row[1]]
    return urls, titles


def save_sent_articles(db_path: Path, articles: list[SummarizedArticle]) -> None:
    if not articles:
        return
    sent_at_utc = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO sent_articles(url, title, sent_at_utc)
            VALUES (?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                sent_at_utc = excluded.sent_at_utc
            """,
            [(article.url, article.title, sent_at_utc) for article in articles],
        )
        conn.commit()

