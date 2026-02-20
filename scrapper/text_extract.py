from __future__ import annotations

from bs4 import BeautifulSoup
import requests
import trafilatura

from scrapper.models import ExtractedContent


def extract_article_text(url: str, timeout_seconds: int) -> ExtractedContent:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if extracted and len(extracted.strip()) > 80:
                return ExtractedContent(text=extracted.strip(), method="trafilatura")
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
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = "\n".join(paragraphs).strip()
        if len(text) > 80:
            return ExtractedContent(text=text, method="requests+bs4")
    except Exception:
        pass

    return ExtractedContent(text="", method="failed")

