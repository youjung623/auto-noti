"""
easylaw.go.kr 법령 페이지 본문 크롤러
RSS 항목의 링크를 받아 실제 법령 내용을 추출합니다.
"""

import re
import requests


BASE_URL = "https://www.easylaw.go.kr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.easylaw.go.kr/",
}


def fetch_law_content(url: str) -> str:
    """
    법령 페이지 URL에서 본문 텍스트를 추출합니다.
    실패 시 빈 문자열을 반환합니다.
    """
    if not url or not url.startswith("http"):
        return ""

    try:
        session = requests.Session()
        # 먼저 메인 페이지를 방문해 쿠키 획득
        session.get(BASE_URL, headers=HEADERS, timeout=15)
        response = session.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
    except requests.RequestException as e:
        print(f"    [크롤링 실패] {url}: {e}")
        return ""

    return _extract_text(response.text)


def _extract_text(html: str) -> str:
    """HTML에서 법령 본문 텍스트를 추출합니다."""
    # 스크립트·스타일·네비게이션 제거
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<nav[^>]*>.*?</nav>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<header[^>]*>.*?</header>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<footer[^>]*>.*?</footer>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # easylaw 본문 영역 우선 추출 (알려진 클래스/id 패턴)
    content = ""
    for pattern in [
        r'<div[^>]*(?:class|id)="[^"]*(?:cont|content|law|body|main)[^"]*"[^>]*>(.*?)</div>',
        r'<article[^>]*>(.*?)</article>',
        r'<main[^>]*>(.*?)</main>',
        r'<div[^>]*id="content"[^>]*>(.*?)</div>',
    ]:
        m = re.search(pattern, html, flags=re.DOTALL | re.IGNORECASE)
        if m and len(m.group(1)) > 200:
            content = m.group(1)
            break

    if not content:
        content = html

    # HTML 태그 제거 후 정리
    text = re.sub(r"<[^>]+>", " ", content)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&[a-z]+;", "", text)
    text = re.sub(r"\s{2,}", "\n", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    # 최대 4000자 (Claude 입력 토큰 절약)
    return text[:4000]
