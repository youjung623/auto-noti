"""
Claude API를 사용해 전자상거래법 변경 항목을 요약·분석합니다.
"""
import anthropic

from law_monitor.config import ANTHROPIC_API_KEY

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """당신은 전자상거래법 및 소비자보호법 전문 법률 분석가입니다.
주어진 법령 변경 또는 보도자료 내용을 분석하여 온라인 사업자가 꼭 알아야 할
핵심 정보를 명확하고 간결하게 요약합니다.
반드시 한국어로 답변하십시오."""

ANALYSIS_TEMPLATE = """다음 전자상거래 관련 법령/보도자료 항목을 분석해주세요.

출처: {source}
제목: {title}
날짜: {date}
URL: {url}
내용: {description}

다음 4가지 항목으로 구조화하여 분석해주세요:
1. **핵심 변경 내용**: 무엇이 바뀌었는지 2-3문장으로 요약
2. **사업자 영향**: 온라인/전자상거래 사업자에게 어떤 영향을 미치는지
3. **대응 필요 사항**: 사업자가 취해야 할 구체적인 조치
4. **시행 예정일**: 언급된 경우 시행 예정일 또는 예고 기간

분석 결과는 HTML 형식으로 작성해주세요 (<h3>, <p>, <ul>, <li> 태그 사용)."""


def analyze_item(item: dict) -> str:
    """단일 항목을 분석하여 HTML 형식의 분석 결과를 반환합니다."""
    prompt = ANALYSIS_TEMPLATE.format(
        source=item.get("source", ""),
        title=item.get("title", ""),
        date=item.get("date", "날짜 미상"),
        url=item.get("url", ""),
        description=item.get("description", "상세 내용 없음"),
    )

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        return f"<p>분석 중 오류 발생: {e}</p>"


def analyze_items(items: list[dict]) -> list[dict]:
    """항목 목록을 분석하여 각 항목에 'analysis' 키를 추가합니다."""
    for item in items:
        print(f"  [AI 분석] {item['title'][:50]}...")
        item["analysis"] = analyze_item(item)
    return items
