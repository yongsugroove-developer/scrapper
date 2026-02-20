from __future__ import annotations

import logging

from openai import OpenAI

from scrapper.models import ScoredArticle, SummaryResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
당신은 한국 부동산/공공분양 정보를 정리하는 리서치 어시스턴트다.
과장하지 말고, 기사 본문에 근거한 사실 위주로 요약하라.
불확실하거나 출처가 애매한 내용은 명확하게 '확인 필요'로 표시하라.
""".strip()


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            content = getattr(item, "content", None)
            if not isinstance(content, list):
                continue
            for part in content:
                text = getattr(part, "text", None)
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        if chunks:
            return "\n".join(chunks)

    return ""


def summarize_article(
    client: OpenAI,
    model: str,
    core_keyword: str,
    article: ScoredArticle,
) -> SummaryResult:
    body_excerpt = article.extracted_text[:9000] if article.extracted_text else ""

    user_prompt = f"""
[핵심 키워드]
{core_keyword}

[문서 제목]
{article.search_result.title}

[문서 스니펫]
{article.search_result.snippet}

[문서 본문 발췌]
{body_excerpt if body_excerpt else "본문 추출 실패"}

[요청 형식]
1) 핵심 요약: 4~6문장
2) 분양/청약 포인트: 최대 3개
3) 확인 필요 사항: 없으면 '없음'
4) 수신자 액션 제안: 1~2문장
모든 응답은 한국어로 작성.
""".strip()

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = _extract_response_text(response)
        if content:
            return SummaryResult(text=content, success=True, reason="ok")
        logger.warning(
            "Summary generation empty output | url=%s model=%s",
            article.canonical_url,
            model,
        )
        return SummaryResult(
            text="요약 생성 실패. 응답이 비어 원문 확인이 필요합니다.",
            success=False,
            reason="empty_output",
        )
    except Exception as exc:
        logger.warning(
            "Summary generation failed | url=%s model=%s error=%s",
            article.canonical_url,
            model,
            exc,
        )

    snippet = article.search_result.snippet.strip()
    body_preview = article.extracted_text.strip()[:400]
    fallback = body_preview if body_preview else snippet
    if not fallback:
        fallback = "본문 추출 실패로 링크 확인이 필요합니다."
    return SummaryResult(
        text=f"요약 생성 실패. 원문 확인 필요.\n핵심 발췌: {fallback}",
        success=False,
        reason="api_error",
    )

