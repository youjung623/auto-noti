"""
공정거래위원회 (ftc.go.kr) — 보도자료 목록 크롤러
"""
import requests
from bs4 import BeautifulSoup

from law_monitor.config import REQUEST_HEADERS, REQUEST_TIMEOUT, KEYWORDS
from law_monitor.utils.storage import make_id

SOURCE = "ftc.go.kr"
BASE_URL = "https://www.ftc.go.kr"

# 보도자료 목록 URL
PRESS_URL = "https://www.ftc.go.kr/www/selectReportUserList.do?key=10&rptTpCd=SRP01"


def _contains_keyword(text: str) -> bool:
    return any(kw in text for kw in KEYWORDS)


def scrape() -> list[dict]:
    """공정거래위원회 보도자료에서 전자상거래 관련 항목을 수집합니다."""
    items = []
    try:
        resp = requests.get(PRESS_URL, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        # 보도자료 목록 파싱
        rows = (
            soup.select("table.brd_list tbody tr")
            or soup.select("ul.press_list li")
            or soup.select("div.list_type ul li")
            or soup.select("table tbody tr")
        )

        for row in rows:
            # 제목 링크
            title_tag = (
                row.select_one("td.subject a")
                or row.select_one("td.title a")
                or row.select_one("a.subject")
                or row.select_one("a")
            )
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            if not title or not _contains_keyword(title):
                continue

            href = title_tag.get("href", "")
            if not href:
                # onclick 속성에서 URL 파라미터 추출 시도
                onclick = title_tag.get("onclick", "")
                if "fn_detail" in onclick or "location.href" in onclick:
                    href = ""  # 동적 URL은 생략
            url = href if href.startswith("http") else (BASE_URL + href if href else PRESS_URL)

            # 날짜
            date_tag = (
                row.select_one("td.date")
                or row.select_one("td:last-child")
                or row.select_one("span.date")
            )
            date = date_tag.get_text(strip=True) if date_tag else ""

            # 부서
            dept_tag = row.select_one("td.dept") or row.select_one("td.writer")
            dept = dept_tag.get_text(strip=True) if dept_tag else ""

            item = {
                "source": SOURCE,
                "title": title,
                "url": url,
                "date": date,
                "description": f"담당부서: {dept}" if dept else "",
                "id": make_id(SOURCE, title, url),
            }
            items.append(item)

    except requests.RequestException as e:
        print(f"[ftc.go.kr] 요청 오류: {e}")
    except Exception as e:
        print(f"[ftc.go.kr] 파싱 오류: {e}")

    return items
