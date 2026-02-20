from __future__ import annotations

from bs4 import BeautifulSoup
import requests
import trafilatura

from scrapper.models import ExtractedContent


def _extract_published_at_from_soup(soup: BeautifulSoup) -> str:
    meta_keys = (
        ("property", "article:published_time"),
        ("property", "og:published_time"),
        ("name", "pubdate"),
        ("name", "publishdate"),
        ("name", "publication_date"),
        ("name", "date"),
        ("name", "dc.date"),
        ("itemprop", "datePublished"),
    )
    for attr, value in meta_keys:
        tag = soup.find("meta", attrs={attr: value})
        if tag:
            content = (tag.get("content") or "").strip()
            if content:
                return content

    time_tag = soup.find("time")
    if time_tag:
        datetime_attr = (time_tag.get("datetime") or "").strip()
        if datetime_attr:
            return datetime_attr
        time_text = time_tag.get_text(" ", strip=True)
        if time_text:
            return time_text

    return ""


def extract_article_text(url: str, timeout_seconds: int) -> ExtractedContent:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted_doc = trafilatura.bare_extraction(
                downloaded,
                include_comments=False,
                include_tables=False,
                url=url,
            )
            if extracted_doc:
                text = (extracted_doc.text or "").strip()
                published_at = (extracted_doc.date or "").strip()
                if len(text) > 80:
                    return ExtractedContent(
                        text=text,
                        method="trafilatura",
                        published_at=published_at,
                    )
    except Exception:
        pass

    try:
        response = requests.get(
            url,
            timeout=timeout_seconds,
            headers={"User-Agent": "Mozilla/5.0 (compatible; daily-digest-bot/1.0)"},
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        published_at = _extract_published_at_from_soup(soup)
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = "\n".join(paragraphs).strip()
        if len(text) > 80:
            return ExtractedContent(
                text=text,
                method="requests+bs4",
                published_at=published_at,
            )
    except Exception:
        pass

    return ExtractedContent(text="", method="failed")

