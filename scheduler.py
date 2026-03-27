"""
로컬/서버 상시 실행 스케줄러
매일 지정 시각에 RSS를 확인하고 이메일을 발송합니다.

실행 방법:
  python scheduler.py             # 기본값: 매일 09:00 실행
  python scheduler.py --time 08:30  # 매일 08:30 실행
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from main import main as run_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scheduler.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

_running = True


def _handle_signal(sig, frame):
    global _running
    log.info("종료 신호 수신 — 스케줄러를 정상 종료합니다.")
    _running = False


def _seconds_until(target_hhmm: str) -> float:
    """지금부터 오늘(또는 내일) target_hhmm 까지 남은 초를 반환합니다."""
    now = datetime.now()
    hh, mm = map(int, target_hhmm.split(":"))
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target <= now:
        # 오늘 시각이 이미 지났으면 내일로
        from datetime import timedelta
        target += timedelta(days=1)
    return (target - now).total_seconds()


def run_scheduler(run_time: str = "09:00") -> None:
    """
    매일 run_time(HH:MM)에 RSS 확인을 실행합니다.
    Ctrl+C 또는 SIGTERM으로 종료합니다.
    """
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    log.info(f"스케줄러 시작 — 매일 {run_time} 에 RSS 확인을 실행합니다.")

    while _running:
        wait_sec = _seconds_until(run_time)
        hh, mm, ss = int(wait_sec // 3600), int((wait_sec % 3600) // 60), int(wait_sec % 60)
        log.info(f"다음 실행까지 {hh}시간 {mm}분 {ss}초 대기 중...")

        # 1분 단위로 sleep하며 종료 신호 체크
        elapsed = 0.0
        while _running and elapsed < wait_sec:
            time.sleep(min(60, wait_sec - elapsed))
            elapsed += 60

        if not _running:
            break

        log.info(f"=== RSS 확인 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
        try:
            exit_code = run_check()
            if exit_code == 0:
                log.info("RSS 확인 완료.")
            else:
                log.error(f"RSS 확인 중 오류 발생 (exit code={exit_code}). 내일 다시 시도합니다.")
        except Exception as e:
            log.exception(f"예상치 못한 오류: {e}")

    log.info("스케줄러 종료.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="easylaw RSS 알림 스케줄러")
    parser.add_argument(
        "--time",
        default="09:00",
        metavar="HH:MM",
        help="매일 실행할 시각 (기본값: 09:00)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)

    args = parse_args()

    # HH:MM 형식 검증
    try:
        hh, mm = args.time.split(":")
        assert 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
    except (ValueError, AssertionError):
        print(f"오류: 시각 형식이 잘못되었습니다 (입력값: {args.time}). HH:MM 형식으로 입력하세요.")
        sys.exit(1)

    run_scheduler(args.time)
