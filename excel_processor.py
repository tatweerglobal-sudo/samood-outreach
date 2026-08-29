import os
import re
import pandas as pd
from typing import List, Dict, Any, Tuple
import database

COMMON_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "hostinger.com"]

def levenshtein_distance(s1: str, s2: str) -> int:
    """حساب مسافة ليفنشتاين بين سلسلتين نصيتين لتحديد الأخطاء الإملائية"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def correct_domain_typo(email: str) -> str:
    """تصحيح الأخطاء الإملائية في دومينات البريد الشائعة"""
    email = email.strip().lower()
    if "@" not in email:
        return email
    
    local_part, domain = email.split("@", 1)
    for common in COMMON_DOMAINS:
        dist = levenshtein_distance(domain, common)
        if 0 < dist <= 2: # إذا كان هناك خطأ إملائي بـ حرف أو حرفين
            return f"{local_part}@{common}"
    return email

def is_valid_email(email: str) -> bool:
    """فحص صيغة البريد الإلكتروني بحسب المعايير القياسية"""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def parse_excel_file(file_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """قراءة وتحليل وتصفية ملف Excel أو CSV وإرجاع الصفوف النظيفة والإحصائيات"""
    if not os.path.exists(file_path):
        raise FileNotFoundError("ملف Excel غير موجود!")

    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif ext == '.csv':
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='gbk')
    else:
        raise ValueError("صيغة الملف غير مدعومة! يرجى رفع ملف Excel أو CSV")

    # تحويل أسماء الأعمدة لنصوص مقصوصة المسافات
    df.columns = [str(c).strip() for c in df.columns]
    
    # محاولة التعرف التلقائي على الأعمدة
    email_col = None
    company_col = None
    contact_col = None
    industry_col = None

    for col in df.columns:
        c_lower = col.lower()
        if not email_col and any(k in c_lower for k in ['email', 'إيميل', 'بريد', 'البريد', 'mail']):
            email_col = col
        elif not company_col and any(k in c_lower for k in ['company', 'شركة', 'الشركة', 'مؤسسة']):
            company_col = col
        elif not contact_col and any(k in c_lower for k in ['name', 'اسم', 'مسؤول', 'مسئول', 'شخص', 'مدير']):
            contact_col = col
        elif not industry_col and any(k in c_lower for k in ['industry', 'sector', 'قطاع', 'مجال', 'نشاط']):
            industry_col = col

    # إذا لم يجد عمود الإيميل بالتطابق، يأخذ أول عمود يحتوي على إيميل
    if not email_col:
        for col in df.columns:
            sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else ""
            if "@" in sample_val:
                email_col = col
                break

    if not email_col:
        raise ValueError("لم يتم العثور على عمود البريد الإلكتروني في ملف الـ Excel!")

    valid_rows = []
    total_raw = len(df)
    invalid_count = 0
    duplicate_in_file = 0
    already_sent_count = 0

    seen_emails = set()

    for idx, row in df.iterrows():
        raw_email = str(row[email_col]).strip() if pd.notna(row[email_col]) else ""
        if not raw_email or raw_email.lower() == 'nan':
            invalid_count += 1
            continue

        # تصحيح الأخطاء الإملائية
        corrected_email = correct_domain_typo(raw_email)

        if not is_valid_email(corrected_email):
            invalid_count += 1
            continue

        # كشف التكرار داخل نفس الملف
        if corrected_email in seen_emails:
            duplicate_in_file += 1
            continue
        seen_emails.add(corrected_email)

        # كشف المراسلة السابقة من قاعدة البيانات
        if database.is_already_sent_or_unsubscribed(corrected_email):
            already_sent_count += 1
            continue

        company_name = str(row[company_col]).strip() if company_col and pd.notna(row[company_col]) else "شركتكم الموقرة"
        contact_name = str(row[contact_col]).strip() if contact_col and pd.notna(row[contact_col]) else "السيد المسؤول"
        industry_name = str(row[industry_col]).strip() if industry_col and pd.notna(row[industry_col]) else "مجال عملكم"

        valid_rows.append({
            "email": corrected_email,
            "company_name": company_name,
            "contact_name": contact_name,
            "industry": industry_name
        })

    stats = {
        "total_raw": total_raw,
        "valid_count": len(valid_rows),
        "invalid_count": invalid_count,
        "duplicate_in_file": duplicate_in_file,
        "already_sent_count": already_sent_count,
        "email_column_detected": email_col,
        "company_column_detected": company_col
    }

    return valid_rows, stats

if __name__ == "__main__":
    print("✅ معالج ملفات Excel وخوارزمية Levenshtein جاهزان للعمل!")
