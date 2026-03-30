"""
전자상거래법 변경 모니터링 — 메인 실행 + 스케줄러
"""
import schedule
import time
from datetime import datetime

from law_monitor.config import CHECK_INTERVAL_HOURS
from law_monitor.scrapers import law_go_kr, moleg, ftc
from law_monitor.utils.storage import filter_new_items
from law_monitor.utils.ai_analyzer import analyze_items
from law_monitor.utils.emailer import send_report


def run_monitor() -> None:
    """크롤링 → 중복 필터 → AI 분석 → 이메일 발송 파이프라인을 실행합니다."""
    print(f"\n{'='*60}")
    print(f"[모니터] 실행 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # 1. 크롤링
    print("\n[1/4] 크롤링 중...")
    all_items: list[dict] = []
    for scraper_module, name in [
        (law_go_kr, "law.go.kr"),
        (moleg, "moleg.go.kr"),
        (ftc, "ftc.go.kr"),
    ]:
        try:
            items = scraper_module.scrape()
            print(f"  {name}: {len(items)}건 수집")
            all_items.extend(items)
        except Exception as e:
            print(f"  {name}: 크롤링 오류 — {e}")

    print(f"  총 수집: {len(all_items)}건")

    # 2. 중복 필터링
    print("\n[2/4] 중복 필터링 중...")
    new_items = filter_new_items(all_items)
    print(f"  새 항목: {len(new_items)}건")

    if not new_items:
        print("\n새로운 항목이 없습니다. 이메일을 발송하지 않습니다.")
        return

    # 3. AI 분석
    print(f"\n[3/4] Claude AI 분석 중... ({len(new_items)}건)")
    analyzed_items = analyze_items(new_items)

    # 4. 이메일 발송
    print("\n[4/4] 이메일 발송 중...")
    send_report(analyzed_items)

    print(f"\n[모니터] 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main() -> None:
    print("전자상거래법 모니터링 시스템 시작")
    print(f"모니터링 주기: {CHECK_INTERVAL_HOURS}시간")

    # 시작 즉시 1회 실행
    run_monitor()

    # 스케줄 등록
    schedule.every(CHECK_INTERVAL_HOURS).hours.do(run_monitor)
    print(f"\n다음 실행까지 대기 중... ({CHECK_INTERVAL_HOURS}시간 간격)")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
