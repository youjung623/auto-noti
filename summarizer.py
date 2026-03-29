"""
Claude API를 이용한 법령 변경 내용 요약 모듈
크롤링한 법령 페이지 텍스트에서 최신 변경 핵심 내용을 추출합니다.
"""

import os
import anthropic


def summarize_law_changes(title: str, raw_text: str) -> str:
    """
    법령 페이지 본문을 받아 최신 변경 내용을 3~5줄로 요약합니다.
    크롤링 실패 등으로 raw_text가 비어 있으면 빈 문자열을 반환합니다.

    필수 환경 변수:
      ANTHROPIC_API_KEY
    """
    if not raw_text.strip():
        return ""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("    [요약 건너뜀] ANTHROPIC_API_KEY 미설정")
        return ""

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""다음은 '쉬운 생활법령' 사이트의 인터넷쇼핑 관련 법령 페이지 내용입니다.

제목: {title}

--- 본문 ---
{raw_text}
--- 끝 ---

위 내용을 읽고, 전자상거래·인터넷쇼핑 사업자 또는 소비자에게 실질적으로 영향을 미치는 \
최신 변경 사항이나 핵심 내용만 골라 아래 형식으로 요약해주세요.

요구사항:
- 3~5개 bullet point (•)
- 각 항목은 1~2문장, 핵심만 간결하게
- 법령 명칭, 시행일, 의무사항, 처벌조항이 있으면 반드시 포함
- 전자상거래와 무관한 내용은 제외
- 요약 외 다른 말은 하지 말 것"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"    [요약 오류] {e}")
        return ""


def enrich_items_with_summary(items: list[dict]) -> list[dict]:
    """
    RSS 항목 리스트를 받아 각 항목에 'ai_summary' 필드를 추가합니다.
    크롤링 + 요약을 순차적으로 수행합니다.
    """
    from content_scraper import fetch_law_content

    for item in items:
        title = item.get("title", "")
        link = item.get("link", "")
        print(f"    본문 크롤링: {title[:40]}...")

        raw_text = fetch_law_content(link)
        if raw_text:
            summary = summarize_law_changes(title, raw_text)
            item["ai_summary"] = summary
        else:
            item["ai_summary"] = ""

    return items
