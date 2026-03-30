import os
from dotenv import load_dotenv

load_dotenv()

# API / 이메일 설정
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "24"))

# Gmail SMTP
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# 모니터링 키워드
KEYWORDS = [
    "전자상거래",
    "전자상거래법",
    "전자상거래 등에서의 소비자보호",
    "통신판매",
    "소비자보호",
    "전자결제",
    "온라인쇼핑",
    "오픈마켓",
]

# 크롤링 대상 URL
URLS = {
    "law_go_kr": "https://www.law.go.kr/lsInfoP.do?lsiSeq=233712#0000",
    "law_go_kr_history": (
        "https://www.law.go.kr/lsInfoP.do?lsiSeq=233712&viewCls=lsRvsDocInfoR"
    ),
    "moleg": "https://www.moleg.go.kr/lawinfo/makingInfo.mo?mid=a10104010000",
    "ftc": "https://www.ftc.go.kr/solution/skin/doc.html?fn=press&rs=/fileupload/data/result/BBSTY1/&bid=71",
    "ftc_news": "https://www.ftc.go.kr/www/selectReportUserList.do?key=10&rptTpCd=SRP01",
}

# 요청 헤더 (봇 차단 우회)
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

REQUEST_TIMEOUT = 15  # seconds

# 저장 파일
SEEN_ITEMS_FILE = "seen_items.json"
