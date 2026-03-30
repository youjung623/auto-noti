"""
seen_items.json으로 이미 처리한 항목을 추적해 중복 알림을 방지합니다.
"""
import json
import hashlib
import os
from datetime import datetime

from law_monitor.config import SEEN_ITEMS_FILE


def _load() -> dict:
    if os.path.exists(SEEN_ITEMS_FILE):
        with open(SEEN_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data: dict) -> None:
    with open(SEEN_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_id(source: str, title: str, url: str = "") -> str:
    """항목의 고유 ID를 생성합니다."""
    raw = f"{source}:{title}:{url}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def is_new(item_id: str) -> bool:
    """해당 ID가 처음 등장하는 항목인지 확인합니다."""
    data = _load()
    return item_id not in data


def mark_seen(item_id: str, meta: dict | None = None) -> None:
    """항목을 처리됨으로 기록합니다."""
    data = _load()
    data[item_id] = {
        "seen_at": datetime.now().isoformat(),
        **(meta or {}),
    }
    _save(data)


def filter_new_items(items: list[dict]) -> list[dict]:
    """
    items 각각에 'id' 키가 있어야 합니다.
    새 항목만 반환하고, 처리된 항목은 seen으로 기록합니다.
    """
    new_items = []
    for item in items:
        item_id = item.get("id") or make_id(
            item.get("source", ""), item.get("title", ""), item.get("url", "")
        )
        item["id"] = item_id
        if is_new(item_id):
            new_items.append(item)
            mark_seen(item_id, {"title": item.get("title"), "source": item.get("source")})
    return new_items
