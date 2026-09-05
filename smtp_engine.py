import smtplib
import imaplib
import ssl
import random
import time
import os
import re
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
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

def convert_markdown_to_prestigious_html(text: str) -> str:
    """تحويل النص إلى تنسيق فاخر واحترافي 100% مع إبراز العناوين والكلمات الهامة ووضع خطوط مذهبة وتحتها بطاقات مميزة"""
    lines = text.split("\n")
    formatted_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("<br>")
            continue

        # العناوين الرئيسية المبرزة بخط سفلي ذهبي وعريض وحجم خط أكبر
        if stripped.startswith("### ") or stripped.startswith("🎯 ") or stripped.startswith("✨ ") or stripped.startswith("📁 "):
            content = stripped.replace("### ", "")
            formatted_line = f'<div style="font-size: 18px; font-weight: 800; color: #e6b455; border-bottom: 2px solid #e6b455; padding-bottom: 6px; margin-top: 18px; margin-bottom: 12px; display: inline-block;">{content}</div>'
        
        # النقاط المميزة والبطاقات الفاخرة (Bullets)
        elif stripped.startswith("🔹 ") or stripped.startswith("✅ ") or stripped.startswith("👉 ") or stripped.startswith("- "):
            formatted_line = f'<div style="background: rgba(255, 255, 255, 0.04); border-right: 4px solid #e6b455; padding: 10px 16px; margin: 8px 0; border-radius: 6px; font-size: 15px; color: #f8fafc; font-weight: 500;">{stripped}</div>'

        # الروابط أو السطور الهامة الأخرى
        elif "https://" in stripped or "http://" in stripped:
            formatted_line = f'<div style="background: rgba(37, 211, 102, 0.1); border: 1px solid rgba(37, 211, 102, 0.4); padding: 12px; margin: 12px 0; border-radius: 8px; text-align: center;">{stripped}</div>'
        
        else:
            formatted_line = f'<div style="margin-bottom: 8px; font-size: 15.5px; color: #f1f5f9;">{stripped}</div>'

        # تحويل **النص العريض** إلى strong ذهبي/أبيض مبرز
        formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #ffffff; background: rgba(230, 180, 85, 0.18); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(230, 180, 85, 0.3); font-weight: bold;">\1</strong>', formatted_line)
        
        # تحويل <u>النص</u> أو _النص_ إلى خط سفلي عريض وبارز جداً
        formatted_line = re.sub(r'<u>(.*?)</u>', r'<u style="color: #e6b455; font-weight: bold; text-underline-offset: 5px; text-decoration-color: #e6b455;">\1</u>', formatted_line)
        
        formatted_lines.append(formatted_line)

    return "".join(formatted_lines)

def build_email_mime(
    sender_name: str,
    sender_email: str,
    recipient_email: str,
    subject: str,
    body_text: str,
    attachment_path: Optional[str] = None,
    is_warmup: bool = False
) -> MIMEMultipart:
    """بناء وتجهيز المراسلة بصيغة MIME مع ترويسات RFC 8058 الحامية من الـ Spam والتنسيق الفاخر"""
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # ترويسات RFC 8058 One-Click Unsubscribe المعيارية لجوجل وميكروسوفت
    server_domain = os.environ.get("SERVER_DOMAIN", "mostafa2510.pythonanywhere.com")
    unsub_url = f"https://{server_domain}/api/unsub?email={recipient_email}"
    unsub_mailto = f"mailto:unsub@{server_domain}?subject=unsubscribe_{recipient_email}"
    msg["List-Unsubscribe"] = f"<{unsub_url}>, <{unsub_mailto}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    body_html_formatted = convert_markdown_to_prestigious_html(body_text)

    if is_warmup:
        # رسائل التسخين تكون نصية بشرية 100% بدون مرفقات صور تجنباً لفلاتر MailChannels [CS]
        html_body = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head><meta charset="utf-8"></head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #0f172a; line-height: 1.7; padding: 20px; direction: rtl; text-align: right;">
            <div>{body_html_formatted}</div>
        </body>
        </html>
        """
        msg_alternative = MIMEMultipart("alternative")
        msg_alternative.attach(MIMEText(body_text, "plain", "utf-8"))
        msg_alternative.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(msg_alternative)
        return msg

    # الهيكل النصي والـ HTML للحملات الرسمية
    banner_cid = "samood_banner_img"
    banner_img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "samood_official_banner.png"))
    if os.path.exists(banner_img_path):
        banner_url = f"cid:{banner_cid}"
    else:
        banner_url = f"https://{server_domain}/samood_official_banner.png"

    whatsapp_url = "https://wa.me/201068158722"
    website_url = "https://www.somodeg.com"

    html_body = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #08140c; font-family: 'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #f8fafc; direction: rtl; text-align: right;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #08140c; padding: 20px 10px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" style="max-width: 600px; background-color: #0f2b18; border: 2px solid #e6b455; border-radius: 16px; overflow: hidden; box-shadow: 0 12px 35px rgba(0,0,0,0.6);" cellspacing="0" cellpadding="0" border="0">
                        
                        <!-- Header Official Banner Infographic Image -->
                        <tr>
                            <td align="center" style="background-color: #1f6132;">
                                <img src="{banner_url}" alt="🏢 مجموعة شركات صمود وسهيل للتوظيف بالخارج (ترخيص 1366 / 596)" style="width: 100%; max-width: 600px; height: auto; display: block; border: 0;" />
                            </td>
                        </tr>

                        <!-- Body Content Area -->
                        <tr>
                            <td style="padding: 30px 25px; line-height: 1.8; font-size: 15px; color: #f1f5f9;">
                                {body_html_formatted}
                            </td>
                        </tr>

                        <!-- Call To Action Buttons (Interactive WhatsApp & Website) -->
                        <tr>
                            <td align="center" style="padding: 10px 25px 30px 25px;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td align="center" style="border-radius: 30px; background: linear-gradient(135deg, #25D366, #128C7E); padding: 2px;">
                                            <a href="{whatsapp_url}" target="_blank" style="background: linear-gradient(135deg, #25D366, #128C7E); color: #ffffff; padding: 15px 30px; border-radius: 30px; font-weight: 800; font-size: 16px; text-decoration: none; display: inline-block; box-shadow: 0 4px 18px rgba(37, 211, 102, 0.5);">
                                                📲 للتواصل المباشر عبر الواتساب (م. مصطفى رياض)
                                            </a>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="center" style="padding-top: 15px;">
                                            <a href="{website_url}" target="_blank" style="color: #e6b455; font-size: 14px; text-decoration: underline; font-weight: bold;">
                                                🌐 زيارة الموقع الرسمي لمجموعة شركات صمود
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Footer Area -->
                        <tr>
                            <td style="background-color: #08140c; padding: 20px; border-top: 1px solid rgba(230, 180, 85, 0.3); text-align: center; font-size: 12px; color: #94a3b8;">
                                <p style="margin: 0 0 8px 0; font-weight: bold; color: #e6b455; font-size: 14px;">مجموعة شركات صمود وسهيل للتوظيف بالخارج (ترخيص رقم 1366 / 596)</p>
                                <p style="margin: 0 0 10px 0;">الدعم اللوجستي وتذاكر الطيران: شركة غاية للسياحة وطيران (ترخيص 1539)</p>
                                <p style="margin: 0;">إذا كنت ترغب في إلغاء الاشتراك من مراسلاتنا، يمكنك <a href="{unsub_url}" style="color: #ef4444; text-decoration: underline;">الضغط هنا لإلغاء الاشتراك</a>.</p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    msg_alternative = MIMEMultipart("alternative")
    msg_alternative.attach(MIMEText(body_text, "plain", "utf-8"))
    msg_alternative.attach(MIMEText(html_body, "html", "utf-8"))
    msg.attach(msg_alternative)

    # إرفاق صورة البانر ضمنياً بصيغة CID للحملات الرسمية
    if os.path.exists(banner_img_path):
        try:
            with open(banner_img_path, "rb") as f:
                img_part = MIMEImage(f.read())
                img_part.add_header('Content-ID', f'<{banner_cid}>')
                img_part.add_header('Content-Disposition', 'inline', filename="samood_official_banner.png")
                msg.attach(img_part)
        except Exception as e:
            print(f"⚠️ تعذر إرفاق صورة البانر الضمنية: {e}")

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
    attachment_path: Optional[str] = None,
    is_warmup: bool = False
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
        attachment_path=attachment_path,
        is_warmup=is_warmup
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
    except smtplib.SMTPAuthenticationError as e:
        err_str = str(e).lower()
        if "suspended" in err_str or "suspicious" in err_str or "compromise" in err_str or "denied" in err_str:
            return False, f"🔴 الحساب معلق مؤقتاً من هوستنجر (Hostinger Suspended): يُرجى الدخول لـ hPanel واختيار Unsuspend أو إعادة تعيين كلمة المرور لتفعيله فوراً. ({str(e)})"
        return False, "فشل الإرسال: خطأ في كلمة مرور الحساب أو تصديق SMTP"
    except Exception as e:
        err_str = str(e).lower()
        if "suspended" in err_str or "suspicious" in err_str or "compromise" in err_str or "denied" in err_str or "554" in err_str:
            return False, f"🔴 الحساب معلق مؤقتاً من هوستنجر (Hostinger Suspended): يُرجى الدخول لـ hPanel واختيار Unsuspend أو إعادة تعيين كلمة المرور لتفعيله فوراً. ({str(e)})"
        return False, f"فشل الإرسال: {str(e)}"

def check_imap_inbox_and_unspam(
    account: Dict[str, Any],
    registered_emails: Optional[List[str]] = None,
    mark_important: bool = True,
    reply_delay_sec: int = 0
) -> Tuple[int, List[str]]:
    """التحقق من علبة الوارد ومجلد الـ Spam عبر IMAP ونقل رسائل التسخين للوارد والرد عليها إيجابياً (Auto-Reply Threading)"""
    import email, email.utils, email.header, random, time
    
    email_addr = account.get("email", "")
    password = account.get("password", "")
    
    if "gmail" in email_addr.lower():
        imap_host = "imap.gmail.com"
    else:
        imap_host = account.get("imap_host") or "imap.hostinger.com"
        
    imap_port = int(account.get("imap_port") or 993)
    
    received_cnt = 0
    actions = []
    reg_set = set([e.lower() for e in (registered_emails or [])])
    
    positive_replies = [
        "أهلاً بك، تم استلام التفاصيل وبمراجعتها سنوافيكم بالتحديثات. شكراً جزيلاً.",
        "تحية طيبة، العرض ممتاز وسنحدد موعد اجتماع قريباً إيقاداً للتعاون.",
        "شكراً على التواصل، تم اعتماد البيانات وإرسالها للإدارة المعنية.",
        "مرحباً بكم، يسعدنا الاطلاع على باقي التخصصات والكوادر المتاحة لديكم."
    ]
    
    try:
        context = ssl.create_default_context()
        with imaplib.IMAP4_SSL(imap_host, imap_port, ssl_context=context) as M:
            M.login(email_addr, password)
            
            # 1. فحص مجلدات الـ Spam لنقل الرسائل للـ INBOX وتدريب الفلاتر (Auto-Unspam)
            for spam_folder in ["Spam", "[Gmail]/Spam", "Junk"]:
                try:
                    res, _ = M.select(f'"{spam_folder}"')
                    if res == 'OK':
                        typ, data = M.search(None, 'ALL')
                        if typ == 'OK' and data[0]:
                            msg_ids = data[0].split()
                            for m_id in msg_ids[-5:]:
                                M.copy(m_id, 'INBOX')
                                M.store(m_id, '+FLAGS', '\\Deleted')
                                received_cnt += 1
                                actions.append(f"📥 تم سحب رسالة تسخين من مجلد {spam_folder} وإعادتها للـ INBOX لتدريب الفلاتر 100%")
                            M.expunge()
                except Exception:
                    pass

            # 2. فحص الـ INBOX وتمييز الرسائل كمقروءة ومهمة والرد التفاعلي الآلي (Auto-Reply Threading)
            auto_replies_sent = 0
            try:
                res, _ = M.select("INBOX")
                if res == 'OK':
                    typ, data = M.search(None, 'ALL')
                    if typ == 'OK' and data[0]:
                        msg_ids = data[0].split()
                        for m_id in msg_ids[-10:]:
                            sender_addr = ""
                            subject_val = "متابعة تسخين"
                            has_answered_flag = False
                            
                            try:
                                res_flags, flag_data = M.fetch(m_id, '(FLAGS)')
                                if res_flags == 'OK' and flag_data:
                                    flags_str = str(flag_data[0])
                                    if '\\Answered' in flags_str:
                                        has_answered_flag = True

                                res_fetch, msg_data = M.fetch(m_id, '(RFC822)')
                                if res_fetch == 'OK' and msg_data:
                                    for resp in msg_data:
                                        if isinstance(resp, tuple):
                                            msg_obj = email.message_from_bytes(resp[1])
                                            raw_from = msg_obj.get("From", "")
                                            sender_addr = email.utils.parseaddr(raw_from)[1].lower()
                                            
                                            raw_subj = msg_obj.get("Subject", "")
                                            dh = email.header.decode_header(raw_subj)
                                            subject_val = "".join([
                                                t.decode(enc or 'utf-8') if isinstance(t, bytes) else str(t)
                                                for t, enc in dh
                                            ])
                            except Exception:
                                pass

                            flags_to_set = '\\Seen \\Flagged' if mark_important else '\\Seen'
                            M.store(m_id, '+FLAGS', flags_to_set)
                            received_cnt += 1

                            # إجراء الرد التفاعلي التلقائي المتعدد الأطراف (Multi-Turn Threaded B2B Dialogue) بحد أقصى رد واحد بالدورة
                            is_from_system_acc = sender_addr and sender_addr != email_addr.lower() and (not reg_set or sender_addr in reg_set)
                            
                            if is_from_system_acc and not has_answered_flag and auto_replies_sent < 1:
                                if reply_delay_sec > 0:
                                    time.sleep(min(reply_delay_sec, 10))

                                thread = database.get_or_create_warmup_thread(sender_addr, email_addr, subject_val)
                                step = thread.get("step_number", 1)
                                
                                turn_2_replies = [
                                    "{GREETING} {SENDER_NAME}،\n\n{تم استلام طلبكم بنجاح|أسعدنا تواصلكم الكريم|جاري مراجعة الطلب} بخصوص {COMPANY}.\n\n{يسرنا إبلاغكم بتوفر الكفاءات المطلوبة جاهزة للمقابلة|يرجى تزويدنا بالأعداد والتخصصات المطلوبة بالتحديد لنرسل لكم السير الذاتية}.\n\n{CLOSER}،\nإدارة التوظيف والاستقدام",
                                    "{GREETING}،\n\n{تحية طيبة، قمنا باطلاعات الإدارة المعنية على خطابكم الموقر|سعداء جداً بفتح آفاق التعاون معكم}.\n\n{هل تودون تحديد موعد اجتماع أونلاين لمناقشة التفاصيل والشروط؟|يرجى الإفادة بالتوقيت المناسب لكم}.\n\n{CLOSER}،\nقسم تطوير الأعمال"
                                ]
                                turn_3_replies = [
                                    "{GREETING}،\n\n{مراعاة للشروط المذكورة، قمنا بتنقية السير الذاتية وتحديد أفضل الكفاءات الحصرية|تم تجهيز ملفات المهندسين والفنيين المطابقة لمتطلبات مشروعكم}.\n\n{يرجى مراجعة الملفات وموافاتنا بموعد المقابلات الحية}.\n\n{CLOSER}،\nفريق الترشيح والمتابعة",
                                    "{GREETING}،\n\n{تم اعتماد التكاليف والضمانات وتحديد موعد السفر المبدئي عبر شركة غاية|تجدون التفاصيل المحدثة معتمدة رسمياً}.\n\n{بانتظار موافقتكم الموقرة لبدء الفحص والتوثيق}.\n\n{CLOSER}،\nإدارة المبيعات والتطوير"
                                ]
                                turn_4_replies = [
                                    "{GREETING}،\n\n{نشكركم على التعاون المثمر، تم اعتماد كافة الترتيبات وإغلاق الملف بنجاح|سعداء بتوقيع هذا التعاون المثمر معكم}.\n\n{سنوافيكم بتحديثات السفر والفيز فور صدورها}.\n\n{CLOSER}،\nالمكتب التنفيذي - مجموعة صمود"
                                ]
                                
                                if step == 1:
                                    raw_rep = random.choice(turn_2_replies)
                                elif step == 2:
                                    raw_rep = random.choice(turn_3_replies)
                                else:
                                    raw_rep = random.choice(turn_4_replies)
                                    
                                import template_engine
                                reply_text = template_engine.enrich_warmup_text(raw_rep, sender_name=account.get("sender_name", ""), target_email=sender_addr)
                                clean_subj_base = subject_val.replace("Re:", "").replace("رد:", "").strip()
                                reply_subj = f"Re: {clean_subj_base}"
                                
                                success_rep, err_rep = send_single_email(account, sender_addr, reply_subj, reply_text, is_warmup=True)
                                if success_rep:
                                    auto_replies_sent += 1
                                    M.store(m_id, '+FLAGS', '\\Answered')
                                    database.advance_warmup_thread(thread["id"])
                                    actions.append(f"💬 تم إرسال رد B2B تفاعلي (مرحلة {step + 1} - {reply_subj}) من {email_addr} إلى {sender_addr} لرفع السمعة 100%!")
                                    database.record_warmup_log(email_addr, sender_addr, reply_subj, reply_text, "SUCCESS", f"AUTO_REPLY_STEP_{step+1}")
                                else:
                                    actions.append(f"⚠️ فشل الرد التفاعلي: {err_rep}")
                                    if "suspended" in err_rep.lower() or "suspicious" in err_rep.lower():
                                        break
            except Exception as e:
                actions.append(f"تنبيه فحص INBOX ({email_addr}): {str(e)}")

            M.logout()
    except Exception as e:
        actions.append(f"تنبيه IMAP ({email_addr}): {str(e)}")

    return received_cnt, actions


if __name__ == "__main__":
    print("✅ محرك الـ SMTP & IMAP الذكي لشركة صمود جاهز ومكتمل!")
