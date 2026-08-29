import smtplib
import ssl
import random
import time
import os
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

import database

class SMTPConnectionError(Exception):
    pass

def verify_dns_mx(domain: str) -> bool:
    """التحقق الاستباقي من وجود خوادم MX حقيقية للدومين لعدم إرسال إيميلات تالفة"""
    try:
        clean_domain = domain.strip().lower()
        records = dns.resolver.resolve(clean_domain, 'MX')
        return len(records) > 0
    except Exception:
        return False

def test_smtp_connection(smtp_host: str, smtp_port: int, use_ssl: bool, email: str, password: str) -> Tuple[bool, str]:
    """اختبار الاتصال بسيرفر الـ SMTP وتصديق المستخدم"""
    try:
        context = ssl.create_default_context()
        if use_ssl or smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=12) as server:
                server.login(email, password)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(email, password)
        return True, "تم الاتصال بالبريد الإلكتروني وتصديق البيانات بنجاح 100%"
    except Exception as e:
        return False, f"فشل الاتصال: {str(e)}"

def build_email_mime(
    sender_name: str,
    sender_email: str,
    recipient_email: str,
    subject: str,
    body_text: str,
    attachment_path: Optional[str] = None
) -> MIMEMultipart:
    """بناء وتجهيز المراسلة بصيغة MIME مع ترويسات RFC 8058 الحامية من الـ Spam"""
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # ترويسات RFC 8058 One-Click Unsubscribe المعيارية لجوجل وميكروسوفت
    unsub_url = f"https://samood.com/api/unsub?email={recipient_email}"
    unsub_mailto = f"mailto:unsub@samood.com?subject=unsubscribe_{recipient_email}"
    msg["List-Unsubscribe"] = f"<{unsub_url}>, <{unsub_mailto}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    # الهيكل النصي والـ HTML
    html_body = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head><meta charset="utf-8"></head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 15px; color: #222222; line-height: 1.6;">
        {body_text.replace('\n', '<br>')}
    </body>
    </html>
    """
    
    msg_alternative = MIMEMultipart("alternative")
    msg_alternative.attach(MIMEText(body_text, "plain", "utf-8"))
    msg_alternative.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(msg_alternative)

    # إضافة المرفق PDF إن وجد
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
        except Exception as e:
            print(f"⚠️ تعذر إرفاق الملف {attachment_path}: {e}")

    return msg

def send_single_email(
    account: Dict[str, Any],
    recipient_email: str,
    subject: str,
    body_text: str,
    attachment_path: Optional[str] = None
) -> Tuple[bool, str]:
    """إرسال إيميل فردي آمن مع التعامل مع كافة أخطاء الشبكة"""
    
    # فحص الـ MX الاستباقي للدومين
    domain = recipient_email.split("@")[-1] if "@" in recipient_email else ""
    if domain and not verify_dns_mx(domain):
        return False, f"الدومين {domain} لا يحتوي على خوادم بريد نشطة (MX Record Invalid)"

    msg = build_email_mime(
        sender_name=account["sender_name"],
        sender_email=account["email"],
        recipient_email=recipient_email,
        subject=subject,
        body_text=body_text,
        attachment_path=attachment_path
    )

    try:
        context = ssl.create_default_context()
        smtp_host = account["smtp_host"]
        smtp_port = int(account["smtp_port"])
        use_ssl = bool(account["use_ssl"])
        email = account["email"]
        password = account["password"]

        if use_ssl or smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=20) as server:
                server.login(email, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(email, password)
                server.send_message(msg)

        # تحديث العداد اليومي للحساب في قاعدة البيانات
        database.increment_account_sent(account["id"])
        return True, "تم الإرسال بنجاح"
    except smtplib.SMTPRecipientsRefused:
        return False, "فشل الإرسال: تم رفض بريد المستلم (Recipient Refused / Bounce)"
    except smtplib.SMTPAuthenticationError:
        return False, "فشل الإرسال: خطأ في كلمة مرور الحساب أو تصديق SMTP"
    except Exception as e:
        return False, f"فشل الإرسال: {str(e)}"

def calculate_gaussian_delay(min_sec: int, max_sec: int) -> float:
    """حساب التأخير الزمني العشوائي بمنحنى جوسيان المحاكي للبشر"""
    mean = (min_sec + max_sec) / 2.0
    std_dev = (max_sec - min_sec) / 4.0
    delay = np.random.normal(mean, std_dev)
    return float(np.clip(delay, min_sec, max_sec))

class CircuitBreaker:
    """قاطع التيار الذكي للتحكم في الحملة وحظر الارتداد العالي"""
    def __init__(self, max_bounce_rate: float = 0.015, window_size: int = 20):
        self.max_bounce_rate = max_bounce_rate
        self.window_size = window_size
        self.history: List[bool] = [] # True للنجاح، False للفشل/Bounce

    def record(self, success: bool):
        self.history.append(success)
        if len(self.history) > self.window_size:
            self.history.pop(0)

    def is_tripped(self) -> bool:
        if len(self.history) < 10:
            return False
        bounces = self.history.count(False)
        rate = bounces / len(self.history)
        return rate >= self.max_bounce_rate

if __name__ == "__main__":
    print("✅ محرك الـ SMTP الذكي لشركة صمود جاهز ومكتمل!")
