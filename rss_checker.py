"""
RSS 피드 조회 및 신규 항목 감지 모듈
easylaw.go.kr RSS 목록 페이지에서 피드를 가져와 새 항목을 확인합니다.
"""

import json
import os
import re
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import xml.etree.ElementTree as ET

import requests


# 이 일수보다 오래된 항목은 무시 (기본 90일)
MAX_ITEM_AGE_DAYS = int(os.environ.get("MAX_ITEM_AGE_DAYS", "90"))

RSS_FEEDS = [
    {
        "title": "인터넷쇼핑",
        "url": "https://www.easylaw.go.kr/CSP/CSP/RssOvRetrieve.laf?csmSeq=835&topMenu=serviceUl7",
    },
]
STATE_FILE = Path("state.json")


def fetch_rss_feed_urls() -> list[dict]:
    """구독 중인 RSS 피드 목록을 반환합니다."""
    return RSS_FEEDS


def fetch_feed_items(feed_url: str) -> list[dict]:
    """RSS 피드에서 항목들을 가져옵니다."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; RSSBot/1.0; +https://github.com)"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9",
    }

    try:
        response = requests.get(feed_url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  [경고] 피드 로딩 실패 ({feed_url}): {e}")
        return []

    return _parse_rss_xml(response.content)


def _parse_rss_xml(content: bytes) -> list[dict]:
    """RSS/Atom XML을 파싱하여 항목 목록을 반환합니다."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"  [경고] XML 파싱 실패: {e}")
        return []

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    items = []

    # RSS 2.0 형식
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "제목 없음").strip()
        link = _to_absolute_url((item.findtext("link") or "").strip())
        description = (item.findtext("description") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        pub_date = (item.findtext("pubDate") or item.findtext("dc:date", namespaces=ns) or "").strip()

        item_id = guid or _make_id(link, title)
        published = _normalize_date(pub_date)

        items.append({
            "id": item_id,
            "title": title,
            "link": link,
            "summary": description,
            "published": published,
        })

    # Atom 형식
    if not items:
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", namespaces=ns) or "제목 없음").strip()
            link_el = entry.find("atom:link", ns)
            link = _to_absolute_url(link_el.get("href", "") if link_el is not None else "")
            summary = (entry.findtext("atom:summary", namespaces=ns) or
                       entry.findtext("atom:content", namespaces=ns) or "").strip()
            entry_id = (entry.findtext("atom:id", namespaces=ns) or "").strip()
            published = (entry.findtext("atom:published", namespaces=ns) or
                         entry.findtext("atom:updated", namespaces=ns) or "").strip()

            items.append({
                "id": entry_id or _make_id(link, title),
                "title": title,
                "link": link,
                "summary": summary,
                "published": published[:19] if published else datetime.now().isoformat(),
            })

    return items


def _to_absolute_url(url: str, base: str = "https://www.easylaw.go.kr") -> str:
    """상대 경로 URL을 절대 URL로 변환합니다."""
    if not url:
        return url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/"):
        return base + url
    return base + "/" + url


def _is_recent(published: str, cutoff: datetime) -> bool:
    """발행일이 cutoff 이후인지 확인합니다."""
    try:
        dt_str = published[:19]  # "YYYY-MM-DDTHH:MM:SS"
        dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        return dt >= cutoff
    except (ValueError, TypeError):
        return True  # 날짜 파싱 실패 시 통과시킴


def _make_id(link: str, title: str) -> str:
    raw = (link + title).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def _normalize_date(date_str: str) -> str:
    """다양한 날짜 형식을 ISO 형식으로 변환합니다."""
    if not date_str:
        return datetime.now().isoformat()
    # RFC 2822 형식 시도
    from email.utils import parsedate
    parsed = parsedate(date_str)
    if parsed:
        try:
            return datetime(*parsed[:6]).isoformat()
        except Exception:
            pass
    return date_str


def load_state() -> dict:
    """이전 실행 상태(확인한 항목 ID)를 파일에서 로드합니다."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    """현재 상태를 파일에 저장합니다."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def check_for_new_items() -> list[dict]:
    """
    RSS 피드를 확인하고 신규 항목 목록을 반환합니다.
    각 항목: {"feed_title", "title", "link", "summary", "published"}
    """
    state = load_state()
    new_items = []

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] RSS 확인 시작...")

    try:
        feeds = fetch_rss_feed_urls()
    except RuntimeError as e:
        print(f"[오류] {e}")
        return []

    print(f"  발견된 피드 수: {len(feeds)}")

    for feed_info in feeds:
        feed_title = feed_info["title"]
        feed_url = feed_info["url"]
        print(f"  피드 확인 중: {feed_title} ({feed_url})")

        items = fetch_feed_items(feed_url)
        seen_ids = set(state.get(feed_url, []))
        new_seen_ids = set(seen_ids)

        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_ITEM_AGE_DAYS)

        for item in items:
            item_id = item["id"]
            if item_id in seen_ids:
                continue

            # 날짜 필터: MAX_ITEM_AGE_DAYS 이내 항목만 허용
            published = item.get("published", "")
            if published and not _is_recent(published, cutoff):
                new_seen_ids.add(item_id)  # 오래된 항목은 조용히 seen 처리
                continue

            new_items.append(
                {
                    "feed_title": feed_title,
                    "feed_url": feed_url,
                    **item,
                }
            )
            new_seen_ids.add(item_id)

        # 최대 500개 ID만 보관 (메모리 관리)
        state[feed_url] = list(new_seen_ids)[-500:]

    save_state(state)

    # 전자상거래 관련 항목만 필터링 + 영향 상품군 태깅
    from ecommerce_filter import filter_and_tag
    new_items = filter_and_tag(new_items)

    print(f"  신규 항목 수 (전자상거래 필터 후): {len(new_items)}")
    return new_items
