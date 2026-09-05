import os
import re
import pandas as pd
from typing import List, Dict, Any, Tuple
import database

COMMON_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "hostinger.com"]

def levenshtein_distance(s1: str, s2: str) -> int:
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
    email = email.strip().lower()
    if "@" not in email:
        return email
    local_part, domain = email.split("@", 1)
    for common in COMMON_DOMAINS:
        dist = levenshtein_distance(domain, common)
        if 0 < dist <= 2:
            return f"{local_part}@{common}"
    return email

def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def find_header_row_and_reframe(df: pd.DataFrame) -> pd.DataFrame:
    """البحث الذكي عن صف الترويسة الحقيقي في أول 10 صفوف وإعادة ضبط الأعمدة"""
    keywords = ['email', 'mail', 'company', 'company_name', 'name', 'sector', 'country', 'id', 'شركة', 'إيميل', 'بريد', 'قطاع', 'دولة', 'اسم']
    
    # فحص الأعمدة الحالية
    current_cols = [str(c).strip().lower() for c in df.columns]
    if any(any(k in col for k in keywords) for col in current_cols):
        return df

    # البحث في أول 10 صفوف داخل البيانات
    for idx in range(min(10, len(df))):
        row_vals = [str(v).strip().lower() for v in df.iloc[idx].values if pd.notna(v)]
        match_count = sum(1 for v in row_vals if any(k in v for k in keywords))
        if match_count >= 2: # إذا احتوى الصف على كلمتين مفتاحيتين أو أكثر
            new_header = [str(v).strip() for v in df.iloc[idx].values]
            new_df = df.iloc[idx + 1:].copy()
            new_df.columns = new_header
            return new_df

    return df

def load_dataframes_dict(file_path: str) -> Dict[str, pd.DataFrame]:
    """تحميل جميع تبويبات الشيت كقاموس مفهرس باسم التبويب"""
    ext = os.path.splitext(file_path)[1].lower()
    sheets_dict = {}

    if ext in ['.xlsx', '.xls']:
        try:
            excel_file = pd.ExcelFile(file_path)
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    if not df.empty:
                        df = find_header_row_and_reframe(df)
                        sheets_dict[sheet_name] = df
                except Exception:
                    pass
        except Exception:
            df = pd.read_excel(file_path)
            df = find_header_row_and_reframe(df)
            sheets_dict["Sheet1"] = df

    elif ext == '.csv':
        encodings = ['utf-8', 'utf-8-sig', 'windows-1256', 'cp1256', 'latin1', 'gbk']
        separators = [',', ';', '\t', '|']
        loaded = False

        for enc in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, encoding=enc, sep=sep)
                    if len(df.columns) >= 1 and not df.empty:
                        df = find_header_row_and_reframe(df)
                        sheets_dict["CSV_Data"] = df
                        loaded = True
                        break
                except Exception:
                    continue
            if loaded:
                break

        if not loaded:
            df = pd.read_csv(file_path, encoding='utf-8', engine='python')
            df = find_header_row_and_reframe(df)
            sheets_dict["CSV_Data"] = df

    return sheets_dict

def parse_excel_file(file_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """قراءة وحظر وتصفية واستخراج الإيميلات من الإكسيل بألغوريثم الفحص الشامل 100%"""
    if not os.path.exists(file_path):
        raise FileNotFoundError("ملف Excel غير موجود!")

    sheets_dict = load_dataframes_dict(file_path)
    if not sheets_dict:
        raise ValueError("الملف فارغ أو يتعذر قراءته!")

    valid_rows = []
    seen_emails = set()
    total_raw = 0
    invalid_count = 0
    duplicate_in_file = 0
    already_sent_count = 0
    preview_sheets = {}

    for sheet_name, df in sheets_dict.items():
        total_raw += len(df)
        df.columns = [str(c).strip() for c in df.columns]
        
        # حفظ عينات معاينة التبويب التفاعلية
        sheet_rows = []
        
        email_cols = []
        company_col = None
        contact_col = None
        industry_col = None

        # 1. التعرف على الأعمدة المتاحة
        for col in df.columns:
            c_norm = str(col).strip().lower().replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ى', 'ي').replace('-', '').replace('_', '').replace(' ', '')
            
            if any(k in c_norm for k in ['email', 'mail', 'بريد', 'ايميل', 'عنوان', 'تواصل', 'to', 'recipient', 'primaryemail', 'secondaryemail']):
                if col not in email_cols:
                    email_cols.append(col)
            elif not company_col and any(k in c_norm for k in ['company', 'companyname', 'شركة', 'مؤسسة', 'منشاة', 'جهة', 'org', 'firm', 'business']):
                company_col = col
            elif not contact_col and any(k in c_norm for k in ['name', 'اسم', 'مسؤول', 'مسئول', 'شخص', 'مدير', 'contact', 'person', 'manager']):
                contact_col = col
            elif not industry_col and any(k in c_norm for k in ['industry', 'sector', 'قطاع', 'مجال', 'نشاط', 'تخصص', 'category']):
                industry_col = col

        # إذا لم يجد عمود إيميل بالاسم، يبحث عن الأعمدة التي تحتوي على @
        if not email_cols:
            for col in df.columns:
                cnt = df[col].astype(str).str.contains('@', na=False).sum()
                if cnt > 0:
                    email_cols.append(col)

        for idx, row in df.iterrows():
            # بناء صف المعاينة للشيت
            row_dict = {}
            for col in df.columns:
                val = str(row[col]).strip() if pd.notna(row[col]) else ""
                row_dict[col] = "" if val.lower() == 'nan' else val
            sheet_rows.append(row_dict)

            # استخراج الإيميلات من الأعمدة المكتشفة (يدعم Primary_Email و Secondary_Email بنفس الوقت!)
            for e_col in email_cols:
                raw_email = str(row[e_col]).strip() if pd.notna(row[e_col]) else ""
                if not raw_email or raw_email.lower() == 'nan' or '@' not in raw_email:
                    continue

                # معالجة الفك إذا كان هناك أكثر من إيميل بنفس الخلية مقسومة بـ فاصلة أو مسافة
                sub_emails = re.split(r'[\s,;/]+', raw_email)
                for sub_e in sub_emails:
                    sub_e = sub_e.strip()
                    if not sub_e or '@' not in sub_e:
                        continue

                    corrected = correct_domain_typo(sub_e)
                    if not is_valid_email(corrected):
                        invalid_count += 1
                        continue

                    if corrected in seen_emails:
                        duplicate_in_file += 1
                        continue
                    seen_emails.add(corrected)

                    if database.is_already_sent_or_unsubscribed(corrected):
                        already_sent_count += 1
                        continue

                    comp_name = str(row[company_col]).strip() if company_col and pd.notna(row[company_col]) and str(row[company_col]).lower() != 'nan' else "شركتكم الموقرة"
                    cont_name = str(row[contact_col]).strip() if contact_col and pd.notna(row[contact_col]) and str(row[contact_col]).lower() != 'nan' else "السيد المسؤول"
                    ind_name = str(row[industry_col]).strip() if industry_col and pd.notna(row[industry_col]) and str(row[industry_col]).lower() != 'nan' else "مجال عملكم"

                    valid_rows.append({
                        "email": corrected,
                        "company_name": comp_name,
                        "contact_name": cont_name,
                        "industry": ind_name
                    })

        preview_sheets[sheet_name] = {
            "columns": list(df.columns),
            "rows": sheet_rows[:150] # أول 150 صف للمعاينة التفاعلية الفاخرة
        }

    # المحاولة 2: المحرك الشامل الكاسح عند عدم كشف الأعمدة الهيكلية
    if not valid_rows:
        email_regex = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
        for sheet_name, df in sheets_dict.items():
            for idx, row in df.iterrows():
                row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
                matches = email_regex.findall(row_str)
                for raw_email in matches:
                    corrected = correct_domain_typo(raw_email)
                    if is_valid_email(corrected) and corrected not in seen_emails:
                        seen_emails.add(corrected)
                        if database.is_already_sent_or_unsubscribed(corrected):
                            already_sent_count += 1
                            continue
                        
                        non_email_vals = [str(val).strip() for val in row.values if pd.notna(val) and raw_email not in str(val) and len(str(val).strip()) > 2]
                        comp = non_email_vals[0] if len(non_email_vals) > 0 else "شركتكم الموقرة"
                        cont = non_email_vals[1] if len(non_email_vals) > 1 else "السيد المسؤول"
                        
                        valid_rows.append({
                            "email": corrected,
                            "company_name": comp,
                            "contact_name": cont,
                            "industry": "عام"
                        })

    if not valid_rows and already_sent_count == 0:
        raise ValueError("لم يتم العثور على أي عنوان بريد إلكتروني (@) في هذا الملف!")

    stats = {
        "total_raw": total_raw,
        "valid_count": len(valid_rows),
        "invalid_count": invalid_count,
        "duplicate_in_file": duplicate_in_file,
        "already_sent_count": already_sent_count,
        "preview_sheets": preview_sheets
    }

    return valid_rows, stats

if __name__ == "__main__":
    print("✅ معالج الإكسيل المطور ودعم البانرات والـ Primary/Secondary Email جاهز 100%!")
