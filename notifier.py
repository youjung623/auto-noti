"""
이메일 알림 발송 모듈
새로운 RSS 항목이 감지되었을 때 이메일을 발송합니다.
"""

import os
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def _get_required_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"환경 변수 '{key}'가 설정되지 않았습니다.")
    return value


def build_html_body(new_items: list[dict]) -> str:
    """신규 항목 목록으로 HTML 이메일 본문을 생성합니다."""
    rows = ""
    for item in new_items:
        title = item.get("title", "제목 없음")
        link = item.get("link", "#")
        feed_title = item.get("feed_title", "")
        published = item.get("published", "")[:10]
        summary = item.get("summary", "")
        if len(summary) > 200:
            summary = summary[:200] + "..."

        products = item.get("affected_products", [])
        product_tags_html = ""
        if products:
            tags = "".join(
                f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;'
                f'background:#fff3e0;color:#e65100;border-radius:4px;font-size:11px;'
                f'font-weight:bold;">🏷 {p}</span>'
                for p in products
            )
            product_tags_html = f'<div style="margin-top:6px;">{tags}</div>'

        rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee;vertical-align:top;">
            <div style="font-size:13px;color:#888;">{feed_title} &nbsp;|&nbsp; {published}</div>
            <div style="margin:4px 0;">
              <a href="{link}" style="font-size:15px;font-weight:bold;color:#1a5fad;text-decoration:none;">
                {title}
              </a>
            </div>
            <div style="font-size:13px;color:#555;">{summary}</div>
            {product_tags_html}
          </td>
        </tr>
        """

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head><meta charset="UTF-8"></head>
    <body style="font-family:'Malgun Gothic',Arial,sans-serif;background:#f4f6f8;margin:0;padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f8;padding:30px 0;">
        <tr><td align="center">
          <table width="640" cellpadding="0" cellspacing="0"
                 style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

            <!-- 헤더 -->
            <tr>
              <td style="background:#1a5fad;padding:24px 28px;">
                <div style="color:#fff;font-size:20px;font-weight:bold;">
                  📋 쉬운 생활법령 업데이트 알림
                </div>
                <div style="color:#b8d0f0;font-size:13px;margin-top:4px;">
                  {now_str} 기준 | 신규 항목 {len(new_items)}건
                </div>
              </td>
            </tr>

            <!-- 본문 -->
            <tr>
              <td style="padding:20px 28px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                  {rows}
                </table>
              </td>
            </tr>

            <!-- 푸터 -->
            <tr>
              <td style="background:#f8f9fa;padding:16px 28px;font-size:12px;color:#aaa;text-align:center;">
                이 메일은 <a href="https://www.easylaw.go.kr" style="color:#1a5fad;">쉬운 생활법령</a> RSS 자동 알림 시스템에서 발송되었습니다.
              </td>
            </tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    return html


def build_plain_body(new_items: list[dict]) -> str:
    """신규 항목 목록으로 plain text 이메일 본문을 생성합니다."""
    lines = [
        "쉬운 생활법령 업데이트 알림",
        f"발송 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"신규 항목: {len(new_items)}건",
        "=" * 60,
    ]
    for item in new_items:
        lines.append(f"\n[{item.get('feed_title', '')}]")
        lines.append(f"제목: {item.get('title', '제목 없음')}")
        lines.append(f"링크: {item.get('link', '')}")
        published = item.get("published", "")[:10]
        if published:
            lines.append(f"날짜: {published}")
        summary = item.get("summary", "")
        if summary:
            wrapped = textwrap.fill(summary[:300], width=72)
            lines.append(f"내용:\n{wrapped}")
        products = item.get("affected_products", [])
        if products:
            lines.append(f"영향 상품군: {', '.join(products)}")
        lines.append("-" * 60)
    return "\n".join(lines)


def send_email(new_items: list[dict]) -> None:
    """
    새 RSS 항목들에 대한 이메일 알림을 발송합니다.

    필수 환경 변수:
      SMTP_HOST      - SMTP 서버 호스트 (예: smtp.gmail.com)
      SMTP_PORT      - SMTP 포트 (예: 587)
      SMTP_USER      - 발신 이메일 주소
      SMTP_PASSWORD  - 이메일 비밀번호 또는 앱 비밀번호
      NOTIFY_EMAIL   - 수신 이메일 주소 (쉼표로 여러 개 지정 가능)
    """
    smtp_host = _get_required_env("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = _get_required_env("SMTP_USER")
    smtp_password = _get_required_env("SMTP_PASSWORD")
    notify_emails_raw = _get_required_env("NOTIFY_EMAIL")
    notify_emails = [e.strip() for e in notify_emails_raw.split(",") if e.strip()]

    subject = f"[쉬운 생활법령] 신규 업데이트 {len(new_items)}건 ({datetime.now().strftime('%Y-%m-%d')})"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(notify_emails)

    msg.attach(MIMEText(build_plain_body(new_items), "plain", "utf-8"))
    msg.attach(MIMEText(build_html_body(new_items), "html", "utf-8"))

    print(f"  이메일 발송 중 → {notify_emails} ...")
    use_ssl = smtp_port == 465

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, notify_emails, msg.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, notify_emails, msg.as_string())

    print("  이메일 발송 완료!")
