"""
Gmail SMTP를 사용해 HTML 이메일을 발송합니다.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from law_monitor.config import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECEIVER,
    SMTP_HOST,
    SMTP_PORT,
)


def _build_html(items: list[dict]) -> str:
    today = datetime.now().strftime("%Y년 %m월 %d일")

    item_blocks = ""
    for item in items:
        source_badge = {
            "law.go.kr": "#1a73e8",
            "moleg.go.kr": "#34a853",
            "ftc.go.kr": "#ea4335",
        }.get(item.get("source", ""), "#666")

        analysis_html = item.get("analysis", "<p>분석 결과 없음</p>")

        item_blocks += f"""
        <div style="
            background:#fff;
            border:1px solid #e0e0e0;
            border-left:4px solid {source_badge};
            border-radius:8px;
            padding:20px 24px;
            margin-bottom:20px;
        ">
            <div style="margin-bottom:10px;">
                <span style="
                    background:{source_badge};
                    color:#fff;
                    font-size:11px;
                    font-weight:bold;
                    padding:3px 8px;
                    border-radius:3px;
                ">{item.get('source', '')}</span>
                <span style="color:#999;font-size:12px;margin-left:10px;">{item.get('date', '')}</span>
            </div>
            <h2 style="margin:0 0 8px;font-size:17px;color:#1a1a1a;">
                <a href="{item.get('url', '#')}" style="color:#1a73e8;text-decoration:none;">
                    {item.get('title', '')}
                </a>
            </h2>
            <div style="color:#444;font-size:14px;line-height:1.7;">
                {analysis_html}
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>전자상거래법 모니터링 리포트</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:'Apple SD Gothic Neo',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:30px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

  <!-- 헤더 -->
  <tr>
    <td style="
        background:linear-gradient(135deg,#1a73e8,#0d47a1);
        padding:28px 32px;
        border-radius:10px 10px 0 0;
    ">
      <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">
        📋 전자상거래법 변경 모니터링
      </h1>
      <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">
        {today} · 새로운 항목 {len(items)}건 감지됨
      </p>
    </td>
  </tr>

  <!-- 본문 -->
  <tr>
    <td style="background:#f5f5f5;padding:24px 16px;">
      {item_blocks}
    </td>
  </tr>

  <!-- 푸터 -->
  <tr>
    <td style="
        background:#fff;
        border:1px solid #e0e0e0;
        border-radius:0 0 10px 10px;
        padding:16px 24px;
        text-align:center;
        color:#999;
        font-size:12px;
    ">
      이 이메일은 전자상거래법 자동 모니터링 시스템에 의해 발송되었습니다.<br>
      법령 정보 출처: law.go.kr · moleg.go.kr · ftc.go.kr
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_report(items: list[dict]) -> bool:
    """분석된 항목 목록을 HTML 이메일로 발송합니다."""
    if not items:
        print("[이메일] 발송할 항목 없음")
        return False

    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        print("[이메일] 환경변수 미설정 (EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER)")
        return False

    today = datetime.now().strftime("%Y.%m.%d")
    subject = f"[전자상거래법 모니터링] 새 변경사항 {len(items)}건 — {today}"
    html_body = _build_html(items)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_bytes())
        print(f"[이메일] 발송 완료 → {EMAIL_RECEIVER} ({len(items)}건)")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[이메일] 인증 오류: Gmail 앱 비밀번호를 확인하세요.")
    except smtplib.SMTPException as e:
        print(f"[이메일] SMTP 오류: {e}")
    except Exception as e:
        print(f"[이메일] 발송 실패: {e}")
    return False
