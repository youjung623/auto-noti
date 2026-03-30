"""
법제처 입법예고 (moleg.go.kr) — 입법예고 목록 크롤러
"""
import requests
from bs4 import BeautifulSoup

from law_monitor.config import REQUEST_HEADERS, REQUEST_TIMEOUT, KEYWORDS
from law_monitor.utils.storage import make_id

SOURCE = "moleg.go.kr"
BASE_URL = "https://www.moleg.go.kr"

# 입법예고 목록 (전자상거래 키워드 검색)
NOTICE_URL = (
    "https://www.moleg.go.kr/lawinfo/makingInfo.mo"
    "?mid=a10104010000"
    "&searchCondition=0"
    "&searchKeyword=%EC%A0%84%EC%9E%90%EC%83%81%EA%B1%B0%EB%9E%98"
    "&pageIndex=1"
)


def _contains_keyword(text: str) -> bool:
    return any(kw in text for kw in KEYWORDS)


def scrape() -> list[dict]:
    """법제처 입법예고 목록에서 전자상거래 관련 항목을 수집합니다."""
    items = []
    try:
        resp = requests.get(NOTICE_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 테이블 행 또는 목록 파싱
        rows = (
            soup.select("table.brd_list tbody tr")
            or soup.select("ul.brd_list li")
            or soup.select("div.list_wrap ul li")
        )

        for row in rows:
            # 제목 셀
            title_tag = (
                row.select_one("td.subject a")
                or row.select_one("td a")
                or row.select_one("a")
            )
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if not title or not _contains_keyword(title):
                continue

            href = title_tag.get("href", "")
            url = href if href.startswith("http") else BASE_URL + href

            # 날짜 셀
            date_cells = row.select("td")
            date = ""
            for cell in date_cells:
                text = cell.get_text(strip=True)
                if len(text) >= 8 and any(c.isdigit() for c in text):
                    date = text
                    break

            # 담당부처
            ministry_tag = row.select_one("td.ministry") or (
                date_cells[1] if len(date_cells) > 1 else None
            )
            ministry = ministry_tag.get_text(strip=True) if ministry_tag else ""

            item = {
                "source": SOURCE,
                "title": title,
                "url": url,
                "date": date,
                "description": f"담당부처: {ministry}" if ministry else "",
                "id": make_id(SOURCE, title, url),
            }
            items.append(item)

    except requests.RequestException as e:
        print(f"[moleg.go.kr] 요청 오류: {e}")
    except Exception as e:
        print(f"[moleg.go.kr] 파싱 오류: {e}")

    return items
