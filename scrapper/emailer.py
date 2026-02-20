from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from scrapper.config import Settings
from scrapper.models import SummarizedArticle


def _nl2br(text: str) -> str:
    return escape(text).replace("\n", "<br>")


def _render_article(index: int, article: SummarizedArticle) -> str:
    return (
        f"<h3>{index}. {escape(article.title)}</h3>"
        f"<p><b>URL:</b> <a href='{escape(article.url)}'>{escape(article.url)}</a></p>"
        f"<p><b>Relevance score:</b> {article.score}</p>"
        f"<p>{_nl2br(article.summary)}</p>"
        "<hr>"
    )


def build_subject(run_at: datetime, keyword: str) -> str:
    return f"[Daily Digest] {run_at.strftime('%Y-%m-%d')} - {keyword}"


def build_html_body(
    run_at: datetime,
    timezone: str,
    keyword: str,
    articles: list[SummarizedArticle],
) -> str:
    header = (
        f"<h2>Daily Crawl Digest</h2>"
        f"<p><b>Run time:</b> {run_at.isoformat()}</p>"
        f"<p><b>Timezone:</b> {escape(timezone)}</p>"
        f"<p><b>Core keyword:</b> {escape(keyword)}</p>"
        f"<p><b>Total items:</b> {len(articles)}</p><hr>"
    )

    if not articles:
        return (
            f"{header}"
            "<p>오늘은 신규 결과가 없습니다. 중복 제거 또는 검색 결과 부족으로 판단됩니다.</p>"
        )

    details = "".join(_render_article(i, article) for i, article in enumerate(articles, start=1))
    return f"{header}{details}"


def send_digest_email(
    settings: Settings,
    run_at: datetime,
    articles: list[SummarizedArticle],
) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = build_subject(run_at, settings.keyword)
    message["From"] = settings.sender_email
    message["To"] = settings.recipient_email

    html_body = build_html_body(run_at, settings.timezone, settings.keyword, articles)
    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_app_password)
        smtp.sendmail(settings.sender_email, [settings.recipient_email], message.as_string())

