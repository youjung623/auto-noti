"""
쉬운 생활법령 RSS 업데이트 이메일 알림 시스템
실행 방법:
  python main.py

환경 변수는 .env 파일 또는 시스템 환경 변수로 설정합니다.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

from rss_checker import check_for_new_items
from notifier import send_email


def main() -> int:
    # .env 파일 로드 (로컬 실행 시)
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print("[INFO] .env 파일 로드 완료")

    new_items = check_for_new_items()

    if not new_items:
        print("[완료] 새로운 항목이 없습니다.")
        return 0

    print(f"[알림] 신규 항목 {len(new_items)}건 발견 — 이메일 발송 시작")
    try:
        send_email(new_items)
    except EnvironmentError as e:
        print(f"[오류] 환경 변수 누락: {e}")
        print("  → .env 파일 또는 GitHub Secrets를 확인하세요.")
        return 1
    except Exception as e:
        print(f"[오류] 이메일 발송 실패: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
