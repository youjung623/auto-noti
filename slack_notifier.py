"""
Slack 알림 발송 모듈
새로운 RSS 항목이 감지되었을 때 Slack 채널로 메시지를 발송합니다.

필수 환경 변수:
  SLACK_WEBHOOK_URL - Slack Incoming Webhook URL
"""

import json
import os
from datetime import datetime

import requests


def send_slack(new_items: list[dict]) -> None:
    """
    새 RSS 항목들을 Slack으로 알립니다.

    Webhook URL 발급:
      Slack 앱 → api.slack.com/apps → Create App
      → Incoming Webhooks → Add New Webhook to Workspace
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise EnvironmentError("환경 변수 'SLACK_WEBHOOK_URL'이 설정되지 않았습니다.")

    blocks = _build_blocks(new_items)

    response = requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        data=json.dumps({"blocks": blocks}),
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Slack 발송 실패 (HTTP {response.status_code}): {response.text}"
        )

    print("  Slack 알림 발송 완료!")


def _build_blocks(new_items: list[dict]) -> list:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📋 쉬운 생활법령 업데이트 알림",
                "emoji": True,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*{now_str} KST*  |  신규 항목 *{len(new_items)}건*",
                }
            ],
        },
        {"type": "divider"},
    ]

    for item in new_items:
        title = item.get("title", "제목 없음")
        link = item.get("link", "")
        feed_title = item.get("feed_title", "")
        published = item.get("published", "")[:10]
        summary = item.get("summary", "")
        if len(summary) > 150:
            summary = summary[:150] + "..."

        title_text = f"*<{link}|{title}>*" if link else f"*{title}*"
        body_text = f"{title_text}\n{summary}"

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": body_text,
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "바로가기", "emoji": True},
                    "url": link,
                    "action_id": "open_link",
                } if link else None,
            }
        )

        # accessory가 None이면 제거
        if blocks[-1]["accessory"] is None:
            del blocks[-1]["accessory"]

        products = item.get("affected_products", [])
        product_text = ("  ·  🏷 " + "  ".join(products)) if products else ""

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📁 {feed_title}  ·  🗓 {published}{product_text}",
                    }
                ],
            }
        )
        blocks.append({"type": "divider"})

    return blocks
