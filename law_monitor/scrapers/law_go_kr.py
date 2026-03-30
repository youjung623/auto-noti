"""
국가법령정보센터 (law.go.kr) — 전자상거래법 개정 이력 크롤러
"""
import requests
from bs4 import BeautifulSoup

from law_monitor.config import REQUEST_HEADERS, REQUEST_TIMEOUT, KEYWORDS
from law_monitor.utils.storage import make_id

SOURCE = "law.go.kr"
BASE_URL = "https://www.law.go.kr"

# 전자상거래 등에서의 소비자보호에 관한 법률 법령 검색 URL
SEARCH_URL = (
    "https://www.law.go.kr/lsSc.do"
    "?menuId=1&subMenuId=15&tabMenuId=81"
    "&eventGubun=060101"
    "&query=%EC%A0%84%EC%9E%90%EC%83%81%EA%B1%B0%EB%9E%98%EB%B2%95"
    "#undefined"
)


def _contains_keyword(text: str) -> bool:
    return any(kw in text for kw in KEYWORDS)


def scrape() -> list[dict]:
    """전자상거래법 관련 법령 개정 이력을 수집합니다."""
    items = []
    try:
        resp = requests.get(SEARCH_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 검색 결과 목록
        rows = soup.select("div.search_list ul li") or soup.select("ul.result_list li")

        for row in rows:
            title_tag = row.select_one("a") or row.select_one(".tit")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if not _contains_keyword(title):
                continue

            href = title_tag.get("href", "")
            url = href if href.startswith("http") else BASE_URL + href

            date_tag = row.select_one(".date") or row.select_one("span.date")
            date = date_tag.get_text(strip=True) if date_tag else ""

            desc_tag = row.select_one(".desc") or row.select_one("p")
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            item = {
                "source": SOURCE,
                "title": title,
                "url": url,
                "date": date,
                "description": desc,
                "id": make_id(SOURCE, title, url),
            }
            items.append(item)

    except requests.RequestException as e:
        print(f"[law.go.kr] 요청 오류: {e}")
    except Exception as e:
        print(f"[law.go.kr] 파싱 오류: {e}")

    return items
