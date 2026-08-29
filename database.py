import sqlite3
import os
import json
import uuid
import hashlib
import datetime
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "samood_data.db")

def hash_password(password: str) -> str:
    salt = "samood_sec_2026_"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 0. جدول مستخدمي النظام والمدير (Admin Users for Cloud Deployment)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 1. جدول حسابات البريد الإلكتروني (SMTP Accounts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS smtp_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        smtp_host TEXT NOT NULL,
        smtp_port INTEGER NOT NULL,
        use_ssl INTEGER DEFAULT 1,
        sender_name TEXT NOT NULL,
        daily_limit INTEGER DEFAULT 45,
        sent_today INTEGER DEFAULT 0,
        last_reset_date TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. جدول قوالب الرسائل (Templates)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        industry TEXT DEFAULT 'عام',
        subject_spintax TEXT NOT NULL,
        body_spintax TEXT NOT NULL,
        attachment_path TEXT,
        is_default INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. جدول سجلات الإرسال ومفاتيح عدم التكرار (Sent Logs & Idempotency)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idempotency_key TEXT UNIQUE NOT NULL,
        recipient_email TEXT NOT NULL,
        company_name TEXT,
        contact_name TEXT,
        industry TEXT,
        account_email TEXT,
        subject_used TEXT,
        status TEXT NOT NULL,
        error_details TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. جدول المستبعدين ومطلبي إلغاء الاشتراك (Unsubscribed / Suppressed)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unsubscribed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        unsubscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. جدول إعدادات الحملة الحالية (Campaign Settings)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaign_settings (
        id INTEGER PRIMARY KEY DEFAULT 1,
        delay_min_seconds INTEGER DEFAULT 45,
        delay_max_seconds INTEGER DEFAULT 90,
        hourly_cap_per_account INTEGER DEFAULT 20,
        working_hours_only INTEGER DEFAULT 1,
        work_start_hour INTEGER DEFAULT 8,
        work_end_hour INTEGER DEFAULT 17,
        warmup_mode INTEGER DEFAULT 0,
        max_bounce_percent REAL DEFAULT 1.5,
        current_status TEXT DEFAULT 'STOPPED'
    );
    """)

    # إدخال مدير النظام الافتراضي (اسم المستخدم: admin | كلمة السر: samood2026)
    cursor.execute("SELECT COUNT(*) as cnt FROM admin_users;")
    if cursor.fetchone()["cnt"] == 0:
        default_pwd_hash = hash_password("samood2026")
        cursor.execute("""
        INSERT INTO admin_users (username, password_hash, display_name)
        VALUES ('admin', ?, 'مدير صمود');
        """, (default_pwd_hash,))

    # إدخال الإعدادات الافتراضية
    cursor.execute("""
    INSERT OR IGNORE INTO campaign_settings (id, delay_min_seconds, delay_max_seconds, hourly_cap_per_account)
    VALUES (1, 45, 90, 20);
    """)

    # إضافة قالب افتراضي مخصص لشركة صمود إذا لم توجد قوالب
    cursor.execute("SELECT COUNT(*) as cnt FROM templates;")
    if cursor.fetchone()["cnt"] == 0:
        default_subject = "{استفسار بخصوص|طلب تواصل لـ|تعاون توظيف مع} {اسم_الشركة}"
        default_body = """{السلام عليكم ورحمة الله وبركاته|تحية طيبة وبعد|أهلاً بكم}،

يسعدنا في شركة **صمود للتوظيف بالخارج والإعارة** أن نعرض على شركتكم الموقرة ({اسم_الشركة}) حلولنا المتكاملة في توفير وتزويد الكوادر والخبرات المصرية {المتخصصة|الاحترافية|المتميزة} في كافة القطاعات ({القطاع}).

نحن نضمن لكم:
- سرعة اختيار وتصفية المرشحين وفق أعلى المعايير.
- إنهاء كافة الإجراءات والترخيص والاعتمادات.
- فترة تجربة وضمان للكوادر المختارة.

هل يمكننا ترتيب اتصال قصير لمناقشة احتياجاتكم القادمة؟

مع خالص الشكر والتقدير،
**فريق العلاقات العامة - شركة صمود**
واتساب/هاتف: +201000000000
الموقع الرسمي: https://samood.com
---
إذا كنت ترغب في إيقاف هذه المراسلات، يرجى الرد بكلمة (توقف)."""

        cursor.execute("""
        INSERT INTO templates (title, industry, subject_spintax, body_spintax, is_default)
        VALUES ('التعريف بخدمات شركة صمود - عام', 'عام', ?, ?, 1);
        """, (default_subject, default_body))

    conn.commit()
    conn.close()

# --- وظائف المصادقة والمستخدمين ---

def verify_admin_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("SELECT * FROM admin_users WHERE username = ? AND password_hash = ?;", (username.strip(), pwd_hash))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def change_admin_password(username: str, new_password: str):
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(new_password)
    cursor.execute("UPDATE admin_users SET password_hash = ? WHERE username = ?;", (pwd_hash, username.strip()))
    conn.commit()
    conn.close()

# --- وظائف التعامل المعتمَدة ---

def get_settings() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaign_settings WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_settings(settings: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE campaign_settings SET
        delay_min_seconds = ?,
        delay_max_seconds = ?,
        hourly_cap_per_account = ?,
        working_hours_only = ?,
        work_start_hour = ?,
        work_end_hour = ?,
        warmup_mode = ?,
        max_bounce_percent = ?
    WHERE id = 1;
    """, (
        settings.get("delay_min_seconds", 45),
        settings.get("delay_max_seconds", 90),
        settings.get("hourly_cap_per_account", 20),
        1 if settings.get("working_hours_only", True) else 0,
        settings.get("work_start_hour", 8),
        settings.get("work_end_hour", 17),
        1 if settings.get("warmup_mode", False) else 0,
        settings.get("max_bounce_percent", 1.5)
    ))
    conn.commit()
    conn.close()

def set_campaign_status(status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE campaign_settings SET current_status = ? WHERE id = 1;", (status,))
    conn.commit()
    conn.close()

def get_active_accounts() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.date.today().isoformat()
    
    cursor.execute("UPDATE smtp_accounts SET sent_today = 0, last_reset_date = ? WHERE last_reset_date IS NULL OR last_reset_date != ?;", (today_str, today_str))
    conn.commit()

    cursor.execute("SELECT * FROM smtp_accounts WHERE is_active = 1 AND sent_today < daily_limit;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def increment_account_sent(account_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE smtp_accounts SET sent_today = sent_today + 1 WHERE id = ?;", (account_id,))
    conn.commit()
    conn.close()

def add_smtp_account(email: str, password: str, smtp_host: str, smtp_port: int, use_ssl: bool, sender_name: str, daily_limit: int = 45):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO smtp_accounts (email, password, smtp_host, smtp_port, use_ssl, sender_name, daily_limit)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (email, password, smtp_host, smtp_port, 1 if use_ssl else 0, sender_name, daily_limit))
    conn.commit()
    conn.close()

def get_all_accounts() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM smtp_accounts ORDER BY id DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_account(account_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM smtp_accounts WHERE id = ?;", (account_id,))
    conn.commit()
    conn.close()

def is_already_sent_or_unsubscribed(email: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    clean_email = email.strip().lower()
    
    cursor.execute("SELECT 1 FROM unsubscribed WHERE LOWER(email) = ?;", (clean_email,))
    if cursor.fetchone():
        conn.close()
        return True
        
    cursor.execute("SELECT 1 FROM sent_logs WHERE LOWER(recipient_email) = ? AND status = 'SENT';", (clean_email,))
    row = cursor.fetchone()
    conn.close()
    return True if row else False

def record_sent_log(recipient_email: str, company_name: str, contact_name: str, industry: str, account_email: str, subject_used: str, status: str, error_details: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    clean_email = recipient_email.strip().lower()
    idempotency_key = f"{clean_email}"
    
    cursor.execute("""
    INSERT OR REPLACE INTO sent_logs (idempotency_key, recipient_email, company_name, contact_name, industry, account_email, subject_used, status, error_details)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (idempotency_key, clean_email, company_name, contact_name, industry, account_email, subject_used, status, error_details))
    conn.commit()
    conn.close()

def add_unsubscribe(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    clean_email = email.strip().lower()
    cursor.execute("INSERT OR IGNORE INTO unsubscribed (email) VALUES (?);", (clean_email,))
    conn.commit()
    conn.close()

def get_templates() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates ORDER BY id DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_template(title: str, industry: str, subject_spintax: str, body_spintax: str, attachment_path: str = None, template_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if template_id:
        cursor.execute("""
        UPDATE templates SET title = ?, industry = ?, subject_spintax = ?, body_spintax = ?, attachment_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?;
        """, (title, industry, subject_spintax, body_spintax, attachment_path, template_id))
    else:
        cursor.execute("""
        INSERT INTO templates (title, industry, subject_spintax, body_spintax, attachment_path)
        VALUES (?, ?, ?, ?, ?);
        """, (title, industry, subject_spintax, body_spintax, attachment_path))
    conn.commit()
    conn.close()

def get_stats() -> Dict[str, int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as sent_count FROM sent_logs WHERE status = 'SENT';")
    sent_count = cursor.fetchone()["sent_count"]
    
    cursor.execute("SELECT COUNT(*) as failed_count FROM sent_logs WHERE status IN ('FAILED', 'BOUNCED');")
    failed_count = cursor.fetchone()["failed_count"]
    
    cursor.execute("SELECT COUNT(*) as unsub_count FROM unsubscribed;")
    unsub_count = cursor.fetchone()["unsub_count"]
    
    conn.close()
    return {
        "sent_count": sent_count,
        "failed_count": failed_count,
        "unsub_count": unsub_count
    }

if __name__ == "__main__":
    init_db()
    print("✅ تم تحديث قاعدة البيانات وإضافة نظام الأمان وتأمين حساب المدير!")
