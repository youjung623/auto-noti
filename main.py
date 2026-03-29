"""
쉬운 생활법령 RSS 업데이트 알림 시스템
이메일 및 Slack으로 신규 항목을 알립니다.

실행 방법:
  python main.py

환경 변수는 .env 파일 또는 시스템 환경 변수로 설정합니다.
이메일/Slack 중 하나만 설정해도 동작합니다.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from rss_checker import check_for_new_items
from notifier import send_email
from slack_notifier import send_slack


def main() -> int:
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print("[INFO] .env 파일 로드 완료")

    new_items = check_for_new_items()

    if not new_items:
        print("[완료] 새로운 항목이 없습니다.")
        return 0

    print(f"[알림] 신규 항목 {len(new_items)}건 발견")

    # 법령 본문 크롤링 + AI 요약
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("[요약] 법령 본문 크롤링 및 AI 요약 시작...")
        from summarizer import enrich_items_with_summary
        new_items = enrich_items_with_summary(new_items)
    else:
        print("  → ANTHROPIC_API_KEY 미설정, AI 요약 건너뜀")

    has_error = False

    # ── 이메일 발송 ──────────────────────────────────────
    if os.environ.get("SMTP_USER"):
        print("  → 이메일 발송 시작")
        try:
            send_email(new_items)
        except EnvironmentError as e:
            print(f"  [오류] 환경 변수 누락: {e}")
            has_error = True
        except Exception as e:
            print(f"  [오류] 이메일 발송 실패: {e}")
            has_error = True
    else:
        print("  → SMTP_USER 미설정, 이메일 발송 건너뜀")

    # ── Slack 발송 ───────────────────────────────────────
    if os.environ.get("SLACK_WEBHOOK_URL"):
        print("  → Slack 발송 시작")
        try:
            send_slack(new_items)
        except Exception as e:
            print(f"  [오류] Slack 발송 실패: {e}")
            has_error = True
    else:
        print("  → SLACK_WEBHOOK_URL 미설정, Slack 발송 건너뜀")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
