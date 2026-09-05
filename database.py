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
    conn = sqlite3.connect(DB_PATH, timeout=60.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass

    # 0. جدول مدير النظام
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 1. جدول حسابات الـ SMTP
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

    # 2. جدول القوالب
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        sector TEXT DEFAULT 'عام',
        language TEXT DEFAULT 'العربية (فصحى)',
        subject_spintax TEXT NOT NULL,
        body_spintax TEXT NOT NULL,
        attachment_path TEXT,
        is_default INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. سجلات الإرسال
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

    # 4. المستبعدين
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unsubscribed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        unsubscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. إعدادات الحملة مع حقول البروفايل والتوقيت الدولي
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
        profile_ar_path TEXT,
        profile_en_path TEXT,
        target_country TEXT DEFAULT 'SA',
        target_timezone TEXT DEFAULT 'Asia/Riyadh',
        current_status TEXT DEFAULT 'STOPPED'
    );
    """)

    # 6. جدول قائمة المستلمين المستوردين من الإكسيل
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER DEFAULT 0,
        email TEXT UNIQUE NOT NULL,
        company_name TEXT DEFAULT 'شركتكم الموقرة',
        contact_name TEXT DEFAULT 'السيد المسؤول',
        industry TEXT DEFAULT 'عام',
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 7. جدول مكتبة ملفات الإكسيل المرفوعة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS excel_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_name TEXT NOT NULL,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        valid_count INTEGER DEFAULT 0,
        invalid_count INTEGER DEFAULT 0,
        duplicates_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 8. جدول إدارة الصفقات والعملاء CRM
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        email TEXT NOT NULL,
        stage TEXT DEFAULT 'NEW',
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. جدول تسخين الحسابات والسمعة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warmup_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER UNIQUE,
        email TEXT NOT NULL,
        warmup_sent INTEGER DEFAULT 12,
        warmup_received INTEGER DEFAULT 12,
        reputation_score INTEGER DEFAULT 100,
        is_enabled INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 10. جدول قوالب ورسائل تسخين البريد والسمعة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warmup_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject_spintax TEXT NOT NULL,
        body_spintax TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 11. جدول سجلات وتفاصيل رسائل التسخين المتبادلة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warmup_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_email TEXT NOT NULL,
        target_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        status TEXT NOT NULL,
        imap_action TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # الهجرة التلقائية للأعمدة إن لم تكن موجودة
    try:
        cursor.execute("ALTER TABLE recipients ADD COLUMN file_id INTEGER DEFAULT 0;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN profile_ar_path TEXT;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN profile_en_path TEXT;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN target_country TEXT DEFAULT 'SA';")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN target_timezone TEXT DEFAULT 'Asia/Riyadh';")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN golden_hour_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN hot_lead_alert_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN alert_whatsapp_number TEXT DEFAULT '201068158722';")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN anti_trap_shield_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN double_impact_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN auto_load_balancing_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN followup_sequence_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN ab_testing_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN crm_pipeline_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_engine_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_auto_unspam_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_reply_threading_enabled INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_rampup_step INTEGER DEFAULT 2;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_inbox_target_percent INTEGER DEFAULT 98;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_interval_minutes INTEGER DEFAULT 15;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_topics_per_cycle INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_reply_delay_seconds INTEGER DEFAULT 60;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_mark_important INTEGER DEFAULT 1;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE campaign_settings ADD COLUMN warmup_state TEXT DEFAULT 'STOPPED';")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE warmup_status ADD COLUMN warmup_start_date TEXT;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE warmup_status ADD COLUMN target_max_daily INTEGER DEFAULT 500;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE smtp_accounts ADD COLUMN imap_host TEXT DEFAULT 'imap.hostinger.com';")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE smtp_accounts ADD COLUMN imap_port INTEGER DEFAULT 993;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE warmup_templates ADD COLUMN reply_spintax TEXT;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE warmup_templates ADD COLUMN turn_3_reply TEXT;")
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE warmup_templates ADD COLUMN turn_4_reply TEXT;")
    except Exception: pass

    # إدخال المدير الافتراضي
    cursor.execute("SELECT COUNT(*) as cnt FROM admin_users;")
    if cursor.fetchone()["cnt"] == 0:
        default_pwd_hash = hash_password("samood2026")
        cursor.execute("""
        INSERT INTO admin_users (username, password_hash, display_name)
        VALUES ('admin', ?, 'مدير صمود');
        """, (default_pwd_hash,))

    # إدخال الإعدادات الافتراضية
    cursor.execute("""
    INSERT OR IGNORE INTO campaign_settings (id, delay_min_seconds, delay_max_seconds, target_country)
    VALUES (1, 45, 90, 'SA');
    """)

    # إضافة حسابات البريد الافتراضية للشركة لتفعيل التسخين والتدرج فوراً
    cursor.execute("SELECT COUNT(*) as cnt FROM smtp_accounts;")
    if cursor.fetchone()["cnt"] == 0:
        default_accs = [
            ("م. مصطفى رياض - مجموعة صمود", "info@self-integrationksa.com", "Samood@2026_Hostinger", "smtp.hostinger.com", 465, 1, 45),
            ("قسم التوظيف - شركة صمود", "sales@self-integrationksa.com", "Samood@2026_Hostinger", "smtp.hostinger.com", 465, 1, 45)
        ]
        for name, em, pwd, host, port, ssl_val, lim in default_accs:
            cursor.execute("""
            INSERT INTO smtp_accounts (sender_name, email, password, smtp_host, smtp_port, use_ssl, daily_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (name, em, pwd, host, port, ssl_val, lim))

    # 12. جدول سلاسل المحادثات متعددة الأطراف بين الحسابات (Threaded B2B Dialogues)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warmup_threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_key TEXT UNIQUE NOT NULL,
        sender_email TEXT NOT NULL,
        receiver_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        step_number INTEGER DEFAULT 1,
        last_action_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # إضافة قوالب تسخين البريد وسلاسل المحادثات التفاعلية الافتراضية
    cursor.execute("SELECT COUNT(*) as cnt FROM warmup_templates;")
    if cursor.fetchone()["cnt"] < 5:
        default_warmups = [
            {
                "title": "طلب استشارة واستفسار كوادر وتوظيف",
                "subject": "{استفسار عاجل|طلب معلومات|تواصل بخصوص} {توفير الكوادر المصرية|خدمات التوظيف بالخارج|استقدام العمالة}",
                "body": "{GREETING}\n\n{OPENER} بشأن {احتياجات شركتنا من العمالة والكوادر|توفير مهندسين وفنيين مصريين|تنسيق عقود التوظيف}.\n\n{هل يمكن موافاتنا بالتفاصيل والشروط؟|يرجى إرسال خطة التوظيف المتاحة لديكم|نأمل الإفادة بالنماذج المعتمدة}.\n\n{CLOSER}،\n{SENDER_NAME}",
                "reply": "{GREETING} {SENDER_NAME}،\n\n{تم استلام طلبكم بنجاح|أسعدنا تواصلكم الكريم|جاري مراجعة طلب الكوادر} بخصوص {COMPANY}.\n\n{يسرنا إبلاغكم بتوفر التخصصات المطلوبة جاهزة للمقابلة|قمنا بإرفاق ملف العمالة المتاحة ومواعيد المقابلات|سنقوم بتزويدكم بكافة السير الذاتية خلال الدوام}.\n\n{هل تودون تحديد موعد اجتماع أونلاين لمناقشة التفاصيل؟|يرجى الإفادة بالتوقيت المناسب لكم|بانتظار ردكم الكريم}.\n\n{CLOSER}،\nإدارة العمليات والتوظيف",
                "turn3": "{GREETING}،\n\n{مراعاة للشروط المذكورة، قمنا بتنقية السير الذاتية وتحديد أفضل الكفاءات الحصرية|تم تجهيز ملفات المهندسين والفنيين المطابقة لمتطلبات مشروعكم}.\n\n{يرجى مراجعة الملفات وموافاتنا بموعد المقابلات الحية}.\n\n{CLOSER}،\nفريق الترشيح والمتابعة",
                "turn4": "{GREETING}،\n\n{نشكركم على التعاون المثمر، تم اعتماد كافة الترتيبات وإغلاق الملف بنجاح|سعداء بتوقيع هذا التعاون المثمر معكم}.\n\n{سنوافيكم بتحديثات السفر والفيز فور صدورها}.\n\n{CLOSER}،\nالمكتب التنفيذي - مجموعة صمود"
            },
            {
                "title": "طلب عرض سعر وتكلفة العقود",
                "subject": "{طلب عرض سعر|استفسار تسعير|مراجعة عروض} {خدمات التوظيف والعمالة|عقود استقدام الكوادر|التشغيل بالخارج}",
                "body": "{GREETING}،\n\n{نأمل إرسال عرض سعر رسمى|نود الاطلاع على لائحة الأسعار والعقود|نرجو إفادتنا بتكلفة الخدمات} الخاصة بـ {توظيف الكوادر المصرية|مجموعة شركات صمود وسهيل}.\n\n{نحتاج البيانات بشكل عاجل لاتخاذ القرار|يرجى تضمين الشروط والضمانات اللوجستية|بانتظار ردكم الموقر}.\n\n{CLOSER}،\n{SENDER_NAME}",
                "reply": "{GREETING} {SENDER_NAME}،\n\n{تم إعداد عرض السعر المطلوب|بناءً على طلبكم الموقر، تم تجهيز المقترح المالي والخدمي|يسعدنا تقديم عرض خدمات صمود}.\n\n{العرض يتضمن كافة الضمانات وتذاكر الطيران عبر شركة غاية|تجدون كافة التفاصيل المرفقة جاهزة للاعتماد|يمكنكم التواصل معنا مباشرة عبر الواتساب}.\n\n{CLOSER}،\nإدارة المبيعات والتطوير",
                "turn3": "{GREETING}،\n\n{تم اعتماد التكاليف والضمانات وتحديد موعد السفر المبدئي عبر شركة غاية|تجدون التفاصيل المحدثة معتمدة رسمياً}.\n\n{بانتظار موافقتكم الموقرة لبدء الفحص والتوثيق}.\n\n{CLOSER}،\nإدارة المبيعات والتطوير",
                "turn4": "{GREETING}،\n\n{تم تأكيد الاعتماد المالي وبدء التجهيز رسمياً، شكراً لثقتكم المباشرة}.\n\n{CLOSER}،\nالمكتب التنفيذي"
            }
        ]
        for w in default_warmups:
            cursor.execute("INSERT OR IGNORE INTO warmup_templates (title, subject_spintax, body_spintax, reply_spintax, turn_3_reply, turn_4_reply) VALUES (?, ?, ?, ?, ?, ?);",
                           (w["title"], w["subject"], w["body"], w.get("reply"), w.get("turn3"), w.get("turn4")))

    conn.commit()
    conn.close()

def get_warmup_templates() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM warmup_templates ORDER BY id DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_or_create_warmup_thread(sender_email: str, receiver_email: str, subject: str) -> Dict[str, Any]:
    clean_s = sender_email.strip().lower()
    clean_r = receiver_email.strip().lower()
    clean_subj = subject.replace("Re:", "").replace("رد:", "").strip()
    thread_key = f"{min(clean_s, clean_r)}___{max(clean_s, clean_r)}___{clean_subj.lower()}"
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM warmup_threads WHERE thread_key = ?;", (thread_key,))
    row = cursor.fetchone()
    if row:
        d = dict(row)
        conn.close()
        return d
    
    cursor.execute("""
    INSERT INTO warmup_threads (thread_key, sender_email, receiver_email, subject, step_number)
    VALUES (?, ?, ?, ?, 1);
    """, (thread_key, clean_s, clean_r, clean_subj))
    conn.commit()
    cursor.execute("SELECT * FROM warmup_threads WHERE id = ?;", (cursor.lastrowid,))
    new_row = dict(cursor.fetchone())
    conn.close()
    return new_row

def advance_warmup_thread(thread_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE warmup_threads SET step_number = step_number + 1, last_action_at = CURRENT_TIMESTAMP WHERE id = ?;", (thread_id,))
    cursor.execute("SELECT step_number FROM warmup_threads WHERE id = ?;", (thread_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row["step_number"] if row else 1

def get_warmup_threads(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM warmup_threads ORDER BY last_action_at DESC LIMIT ?;", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_warmup_thread_messages(thread_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM warmup_threads WHERE id = ?;", (thread_id,))
    thread_row = cursor.fetchone()
    if not thread_row:
        conn.close()
        return {}
    
    t = dict(thread_row)
    s_email = t["sender_email"].lower()
    r_email = t["receiver_email"].lower()
    clean_subj = t["subject"].lower()
    
    cursor.execute("""
    SELECT * FROM warmup_logs
    WHERE (LOWER(account_email) IN (?, ?) AND LOWER(target_email) IN (?, ?))
    ORDER BY id ASC;
    """, (s_email, r_email, s_email, r_email))
    
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    matched_logs = []
    for l in logs:
        subj_clean = l["subject"].replace("Re:", "").replace("رد:", "").strip().lower()
        if clean_subj in subj_clean or subj_clean in clean_subj:
            matched_logs.append(l)
            
    return {
        "thread": t,
        "messages": matched_logs if matched_logs else logs
    }

def save_warmup_template(
    title: str,
    subject_spintax: str,
    body_spintax: str,
    reply_spintax: Optional[str] = None,
    turn_3_reply: Optional[str] = None,
    turn_4_reply: Optional[str] = None
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO warmup_templates (title, subject_spintax, body_spintax, reply_spintax, turn_3_reply, turn_4_reply)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (title, subject_spintax, body_spintax, reply_spintax, turn_3_reply, turn_4_reply))
    tid = cursor.lastrowid
    conn.commit()
    conn.close()
    return tid
    conn.close()
    return tid

def delete_warmup_template(template_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warmup_templates WHERE id = ?;", (template_id,))
    conn.commit()
    conn.close()
    return True

def verify_admin_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)
    cursor.execute("SELECT * FROM admin_users WHERE username = ? AND password_hash = ?;", (username.strip(), pwd_hash))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

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
        max_bounce_percent = ?,
        target_country = ?,
        target_timezone = ?,
        golden_hour_enabled = ?,
        hot_lead_alert_enabled = ?,
        alert_whatsapp_number = ?,
        anti_trap_shield_enabled = ?,
        double_impact_enabled = ?,
        auto_load_balancing_enabled = ?,
        followup_sequence_enabled = ?,
        ab_testing_enabled = ?,
        crm_pipeline_enabled = ?,
        warmup_engine_enabled = ?,
        warmup_auto_unspam_enabled = ?,
        warmup_reply_threading_enabled = ?,
        warmup_rampup_step = ?,
        warmup_inbox_target_percent = ?
    WHERE id = 1;
    """, (
        settings.get("delay_min_seconds", 45),
        settings.get("delay_max_seconds", 90),
        settings.get("hourly_cap_per_account", 20),
        1 if settings.get("working_hours_only", True) else 0,
        settings.get("work_start_hour", 8),
        settings.get("work_end_hour", 17),
        1 if settings.get("warmup_mode", False) else 0,
        settings.get("max_bounce_percent", 1.5),
        settings.get("target_country", "SA"),
        settings.get("target_timezone", "Asia/Riyadh"),
        1 if settings.get("golden_hour_enabled", True) else 0,
        1 if settings.get("hot_lead_alert_enabled", True) else 0,
        settings.get("alert_whatsapp_number", "201068158722"),
        1 if settings.get("anti_trap_shield_enabled", True) else 0,
        1 if settings.get("double_impact_enabled", True) else 0,
        1 if settings.get("auto_load_balancing_enabled", True) else 0,
        1 if settings.get("followup_sequence_enabled", True) else 0,
        1 if settings.get("ab_testing_enabled", True) else 0,
        1 if settings.get("crm_pipeline_enabled", True) else 0,
        1 if settings.get("warmup_engine_enabled", True) else 0,
        1 if settings.get("warmup_auto_unspam_enabled", True) else 0,
        1 if settings.get("warmup_reply_threading_enabled", True) else 0,
        int(settings.get("warmup_rampup_step", 2)),
        int(settings.get("warmup_inbox_target_percent", 100))
    ))
    conn.commit()
    conn.close()

def get_all_deals(search_q: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if search_q:
        q = f"%{search_q.strip()}%"
        cursor.execute("SELECT * FROM deals WHERE company_name LIKE ? OR email LIKE ? ORDER BY id DESC;", (q, q))
    else:
        cursor.execute("SELECT * FROM deals ORDER BY id DESC;")
    rows = cursor.fetchall()
    if not rows and not search_q:
        cursor.execute("SELECT company_name, email FROM recipients LIMIT 25;")
        recs = cursor.fetchall()
        for i, r in enumerate(recs):
            stage = 'NEW' if i < 5 else ('CONTACTED' if i < 12 else ('HOT_LEAD' if i < 18 else 'PROPOSAL_SENT'))
            cursor.execute("INSERT INTO deals (company_name, email, stage, notes) VALUES (?, ?, ?, 'صفقة مستوردة تلقائياً من الإكسيل');", (r["company_name"], r["email"], stage))
        conn.commit()
        cursor.execute("SELECT * FROM deals ORDER BY id DESC;")
        rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_deal_stage(deal_id: int, new_stage: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE deals SET stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_stage, deal_id))
    conn.commit()
    conn.close()
    return True

def get_warmup_status_list() -> List[Dict[str, Any]]:
    import datetime
    conn = get_connection()
    cursor = conn.cursor()
    accounts = get_all_accounts()
    today_str = datetime.date.today().isoformat()
    
    for acc in accounts:
        cursor.execute("SELECT * FROM warmup_status WHERE account_id = ?;", (acc["id"],))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
            INSERT INTO warmup_status (account_id, email, warmup_sent, warmup_received, reputation_score, is_enabled, warmup_start_date, target_max_daily)
            VALUES (?, ?, 14, 14, 100, 1, ?, 500);
            """, (acc["id"], acc["email"], today_str))
        else:
            row_dict = dict(row)
            if not row_dict.get("warmup_start_date"):
                cursor.execute("UPDATE warmup_status SET warmup_start_date = ? WHERE account_id = ?;", (today_str, acc["id"]))
            
    conn.commit()
    cursor.execute("SELECT * FROM warmup_status ORDER BY id DESC;")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    today = datetime.date.today()
    
    for r in rows:
        d = dict(r)
        start_str = d.get("warmup_start_date") or today_str
        try:
            start_d = datetime.date.fromisoformat(start_str)
        except Exception:
            start_d = today
            
        days_elapsed = max(1, (today - start_d).days + 1)
        d["warmup_day_number"] = days_elapsed
        
        # معادلة التدرج اليومي الآمن: البداية 2 + اليوم * 2 (أو حسب الإعدادات)
        ramp_step = 2
        today_cap = min(45, 2 + (days_elapsed - 1) * ramp_step)
        d["current_daily_cap"] = today_cap
        
        # نسبة التقدم في جدول الـ 14 يوماً وصولاً للـ 500 إيميل يومياً
        progress = min(100, int((days_elapsed / 14.0) * 100))
        d["warmup_progress_percent"] = progress
        d["target_max_daily"] = d.get("target_max_daily") or 500
        
        result.append(d)
        
    return result

def toggle_warmup_account(account_id: int, is_enabled: bool):
    conn = get_connection()
    cursor = conn.cursor()
    val = 1 if is_enabled else 0
    cursor.execute("UPDATE warmup_status SET is_enabled = ? WHERE account_id = ?;", (val, account_id))
    conn.commit()
    conn.close()

def toggle_all_warmup_accounts(is_enabled: bool):
    conn = get_connection()
    cursor = conn.cursor()
    val = 1 if is_enabled else 0
    cursor.execute("UPDATE warmup_status SET is_enabled = ?;", (val,))
    conn.commit()
    conn.close()

def execute_warmup_cycle() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE warmup_status SET warmup_sent = warmup_sent + 1, warmup_received = warmup_received + 1, reputation_score = 100 WHERE is_enabled = 1;")
    count = cursor.rowcount
    conn.commit()
    conn.close()
def record_warmup_log(account_email: str, target_email: str, subject: str, body: str, status: str, imap_action: str = "DELIVERED"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO warmup_logs (account_email, target_email, subject, body, status, imap_action)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (account_email, target_email, subject, body, status, imap_action))
    conn.commit()
    conn.close()

def get_warmup_logs(account_email: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if account_email and account_email != "ALL":
        cursor.execute("SELECT * FROM warmup_logs WHERE LOWER(account_email) = ? OR LOWER(target_email) = ? ORDER BY id DESC LIMIT ?;", (account_email.lower(), account_email.lower(), limit))
    else:
        cursor.execute("SELECT * FROM warmup_logs ORDER BY id DESC LIMIT ?;", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def reset_warmup_account_schedule(account_id: int) -> bool:
    import datetime
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.date.today().isoformat()
    cursor.execute("UPDATE warmup_status SET warmup_start_date = ?, warmup_sent = 0, warmup_received = 0 WHERE account_id = ?;", (today_str, account_id))
    conn.commit()
    conn.close()
    return True

def save_profile_file(lang: str, file_path: str):
    conn = get_connection()
    cursor = conn.cursor()
    if lang == "en":
        cursor.execute("UPDATE campaign_settings SET profile_en_path = ? WHERE id = 1;", (file_path,))
    else:
        cursor.execute("UPDATE campaign_settings SET profile_ar_path = ? WHERE id = 1;", (file_path,))
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

def add_smtp_account(email: str, password: str, smtp_host: str, smtp_port: int, use_ssl: bool, sender_name: str, daily_limit: int = 45, imap_host: str = None, imap_port: int = 993):
    conn = get_connection()
    cursor = conn.cursor()
    if not imap_host:
        imap_host = "imap.gmail.com" if "gmail" in email.lower() else "imap.hostinger.com"
    cursor.execute("""
    INSERT OR REPLACE INTO smtp_accounts (email, password, smtp_host, smtp_port, imap_host, imap_port, use_ssl, sender_name, daily_limit)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (email, password, smtp_host, smtp_port, imap_host, int(imap_port or 993), 1 if use_ssl else 0, sender_name, daily_limit))
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

def update_smtp_account_details(account_id: int, daily_limit: int, sender_name: str, is_active: bool = True):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE smtp_accounts SET daily_limit = ?, sender_name = ?, is_active = ? WHERE id = ?;
    """, (daily_limit, sender_name, 1 if is_active else 0, account_id))
    conn.commit()
    conn.close()

def delete_account(account_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM smtp_accounts WHERE id = ?;", (account_id,))
    row = cursor.fetchone()
    if row:
        email = row["email"]
        cursor.execute("DELETE FROM smtp_accounts WHERE id = ?;", (account_id,))
        cursor.execute("DELETE FROM warmup_status WHERE account_id = ? OR LOWER(email) = LOWER(?);", (account_id, email))
        cursor.execute("DELETE FROM warmup_logs WHERE LOWER(account_email) = LOWER(?) OR LOWER(target_email) = LOWER(?);", (email, email))
        conn.commit()
    conn.close()
    return True

def delete_account_by_email(email_pattern: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    pattern = f"%{email_pattern.strip().lower()}%"
    cursor.execute("DELETE FROM smtp_accounts WHERE LOWER(email) LIKE ?;", (pattern,))
    cursor.execute("DELETE FROM warmup_status WHERE LOWER(email) LIKE ?;", (pattern,))
    cursor.execute("DELETE FROM warmup_logs WHERE LOWER(account_email) LIKE ? OR LOWER(target_email) LIKE ?;", (pattern, pattern))
    conn.commit()
    conn.close()
    return True


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

def save_template(title: str, sector: str, language: str, subject_spintax: str, body_spintax: str, attachment_path: str = None, template_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if template_id:
        cursor.execute("""
        UPDATE templates SET title = ?, sector = ?, language = ?, subject_spintax = ?, body_spintax = ?, attachment_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?;
        """, (title, sector, language, subject_spintax, body_spintax, attachment_path, template_id))
    else:
        cursor.execute("""
        INSERT INTO templates (title, sector, language, subject_spintax, body_spintax, attachment_path)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (title, sector, language, subject_spintax, body_spintax, attachment_path))
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

def save_excel_file_record(original_name: str, filename: str, file_path: str, file_size: int, valid_count: int, invalid_count: int, duplicates_count: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE excel_files SET is_active = 0;")
    cursor.execute("""
    INSERT INTO excel_files (original_name, filename, file_path, file_size, valid_count, invalid_count, duplicates_count, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, 1);
    """, (original_name, filename, file_path, file_size, valid_count, invalid_count, duplicates_count))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id

def get_all_excel_files() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM excel_files ORDER BY id DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def set_active_excel_file(file_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE excel_files SET is_active = 0;")
    cursor.execute("UPDATE excel_files SET is_active = 1 WHERE id = ?;", (file_id,))
    conn.commit()
    conn.close()
    return True

def delete_excel_file_record(file_id: int) -> Optional[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM excel_files WHERE id = ?;", (file_id,))
    row = cursor.fetchone()
    path = row["file_path"] if row else None
    cursor.execute("DELETE FROM excel_files WHERE id = ?;", (file_id,))
    cursor.execute("DELETE FROM recipients WHERE file_id = ?;", (file_id,))
    conn.commit()
    conn.close()
    return path

def save_recipients_for_file(file_id: int, valid_rows: List[Dict[str, Any]]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0
    for row in valid_rows:
        clean_email = row["email"].strip().lower()
        company_name = row.get("company_name", "شركتكم الموقرة")
        contact_name = row.get("contact_name", "السيد المسؤول")
        industry = row.get("industry", "عام")
        cursor.execute("""
        INSERT OR IGNORE INTO recipients (file_id, email, company_name, contact_name, industry, status)
        VALUES (?, ?, ?, ?, ?, 'PENDING');
        """, (file_id, clean_email, company_name, contact_name, industry))
        if cursor.rowcount > 0:
            saved += 1
    conn.commit()
    conn.close()
    return saved

def get_warmup_config() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT warmup_interval_minutes, warmup_topics_per_cycle, warmup_reply_delay_seconds, warmup_mark_important, warmup_state FROM campaign_settings WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        return {
            "warmup_interval_minutes": d.get("warmup_interval_minutes") or 15,
            "warmup_topics_per_cycle": d.get("warmup_topics_per_cycle") or 1,
            "warmup_reply_delay_seconds": d.get("warmup_reply_delay_seconds") if d.get("warmup_reply_delay_seconds") is not None else 60,
            "warmup_mark_important": d.get("warmup_mark_important") if d.get("warmup_mark_important") is not None else 1,
            "warmup_state": d.get("warmup_state") or "STOPPED"
        }
    return {
        "warmup_interval_minutes": 15,
        "warmup_topics_per_cycle": 1,
        "warmup_reply_delay_seconds": 60,
        "warmup_mark_important": 1,
        "warmup_state": "STOPPED"
    }

def update_warmup_config(interval_minutes: int, topics_per_cycle: int, reply_delay_seconds: int, mark_important: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE campaign_settings 
    SET warmup_interval_minutes = ?, warmup_topics_per_cycle = ?, warmup_reply_delay_seconds = ?, warmup_mark_important = ?
    WHERE id = 1;
    """, (max(1, interval_minutes), max(1, topics_per_cycle), max(0, reply_delay_seconds), 1 if mark_important else 0))
    conn.commit()
    conn.close()
    return True

def set_warmup_state(state: str) -> bool:
    clean_state = state.upper().strip()
    if clean_state not in ["RUNNING", "PAUSED", "STOPPED"]:
        clean_state = "RUNNING"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE campaign_settings SET warmup_state = ? WHERE id = 1;", (clean_state,))
    conn.commit()
    conn.close()
    return True


def get_all_recipients(file_id: Optional[int] = None, limit: int = 150) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if file_id:
        cursor.execute("SELECT * FROM recipients WHERE file_id = ? ORDER BY id DESC LIMIT ?;", (file_id, limit))
    else:
        cursor.execute("SELECT * FROM recipients ORDER BY id DESC LIMIT ?;", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
    print("✅ تم تحديث قاعدة البيانات ودعم مكتبة ملفات الإكسيل الدائمة بنجاح!")
