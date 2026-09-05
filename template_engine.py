import re
import random
from typing import Dict, List, Optional

SPAM_TRIGGER_WORDS = [
    "مجاناً", "مجانا", "فرصة لا تعوض", "ربح سريع", "100% مضمون",
    "ضمان 100%", "اضغط هنا", "ارسل اموال", "ثراء", "عرض خاص جدا"
]

def generate_unique_opener(lang_or_dialect: str = "ar_fusha", company_name: str = "شركتكم الموقرة") -> str:
    """توليد مطلع وافتتاحية فريدة وديناميكية 100% تضمن عدم تكرار أية رسالتين إطلاقاً"""
    
    # 1. التحيات الأولية
    greetings_ar = [
        f"تحية طيبة وبعد لسيادتكم في {company_name}،",
        f"السلام عليكم ورحمة الله وبركاته لمقام {company_name}،",
        f"أهلاً وسهلاً بفريق العمل في {company_name}،",
        f"أسعد الله جميع أوقاتكم في {company_name}،",
        f"تحياتنا العطرة لكم في شركة {company_name}،"
    ]
    
    # 2. الجمل الممهدة
    bridges_ar = [
        "نلتقي معكم اليوم لبحث أفق التعاون التشاركي في رفد مشاريعكم بأفضل الخبرات والكوادر المصرية.",
        "يسعدنا التواصل معكم وإتاحة خدماتنا الاستثنائية لتزويد منشأتكم بالعمالة المصرية المتميزة.",
        "نتشرف بالتعرف على مشاريعكم وتوفير احتياجاتكم التوظيفية بسرعة ودقة عالية.",
        "نسعد بتقديم نموذج تعاوننا الفعال لمساندة تطلعاتكم ونمو أعمالكم في المنطقة.",
        "يطيب لنا إحاطتكم بخدماتنا التخصصية في استقطاب وإعارة الخبرات المصرية المؤهلة."
    ]
    
    greetings_en = [
        f"Dear Hiring & Management Team at {company_name},",
        f"Warm greetings to the leadership team at {company_name},",
        f"Hello to the management team at {company_name},"
    ]
    bridges_en = [
        "We are writing to introduce our premier manpower & recruitment solutions tailored for your business expansion.",
        "It is our pleasure to connect with your esteemed organization to support your workforce and recruitment needs.",
        "We welcome the opportunity to present our specialized talent supply services designed for leading companies like yours."
    ]

    greetings_fr = [
        f"Bonjour à toute l'équipe de {company_name},",
        f"Chère direction de {company_name},"
    ]
    bridges_fr = [
        "Nous avons le plaisir de vous présenter nos solutions spécialisées de recrutement et fourniture de main-d'œuvre.",
        "C'est un honneur de prendre contact avec votre entreprise pour vous accompagner dans vos besoins en capital humain."
    ]

    if "English" in lang_or_dialect or "en" in lang_or_dialect:
        return f"{random.choice(greetings_en)}\n\n{random.choice(bridges_en)}"
    elif "French" in lang_or_dialect or "fr" in lang_or_dialect:
        return f"{random.choice(greetings_fr)}\n\n{random.choice(bridges_fr)}"
    else:
        return f"{random.choice(greetings_ar)}\n\n{random.choice(bridges_ar)}"

def parse_spintax(text: str) -> str:
    """فك ومعالجة الـ Spintax المتبادل بصيغة {نص1|نص2|نص3} عشوائياً وبأسلوب متداخل"""
    pattern = r"\{([^{}]+)\}"
    while re.search(pattern, text):
        match_found = False
        def replace_match(match):
            nonlocal match_found
            content = match.group(1)
            if "|" in content:
                match_found = True
                choices = content.split("|")
                return random.choice(choices)
            return match.group(0) # الإبقاء على المتغيرات غير المسبوقة
        
        new_text = re.sub(pattern, replace_match, text)
        if not match_found:
            break
        text = new_text
    return text

def render_template(
    template_spintax: str,
    context: Dict[str, str],
    add_unique_opener: bool = True
) -> str:
    """توليد النص النهائي بعد استبدال المتغيرات وفك الـ Spintax مع دمج الافتتاحية الفريدة"""
    company_name = context.get("company_name") or "شركتكم الموقرة"
    contact_name = context.get("contact_name") or "السيد المسؤول"
    industry = context.get("industry") or "مجال عملكم"

    rendered = template_spintax.replace("{اسم_الشركة}", company_name)
    rendered = rendered.replace("{اسم_المسؤول}", contact_name)
    rendered = rendered.replace("{القطاع}", industry)
    rendered = rendered.replace("{المجال}", industry)
    
    # 2. فك الـ Spintax
    rendered = parse_spintax(rendered)
    
    # 3. دمج الافتتاحية العشوائية الفريدة لمنع الـ Spam
    if add_unique_opener:
        opener = generate_unique_opener(context.get("language", "ar_fusha"), company_name)
        # إذا كانت الرسالة تبدأ بتحية شائعة، نستبدل المطلع بـ opener الفريد
        rendered = f"{opener}\n\n{rendered}"

    return rendered

def check_spam_keywords(text: str) -> List[str]:
    """فحص النص وإرجاع أي كلمات قد تثير شكوك فلاتر الـ Spam"""
    found_triggers = []
    for word in SPAM_TRIGGER_WORDS:
        if word in text:
            found_triggers.append(word)
    return found_triggers

def enrich_warmup_text(text: str, sender_name: str = "", target_email: str = "", company_name: str = "شركة صمود الدولية") -> str:
    """معالجة وتوليد نص رسالة تسخين فريدة 100% مع استبدال كافة المتغيرات الديناميكية والـ Spintax المتداخل"""
    import datetime, random
    
    now = datetime.datetime.now()
    days_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    day_name = days_ar[now.weekday()]
    date_str = now.strftime("%Y-%m-%d %H:%M")
    time_str = now.strftime("%H:%M")
    ref_no = f"REF-{random.randint(10000, 99999)}"
    
    cities = ["القاهرة", "الرياض", "جدة", "الدمام", "دبي", "أبوظبي", "الدوحة", "الكويت"]
    sectors = ["المقاولات والتشييد", "الموارد البشرية والتأهيل", "الخدمات اللوجستية والطيران", "التشغيل والصيانة"]
    
    city = random.choice(cities)
    sector = random.choice(sectors)
    
    greetings = "{تحية طيبة وبعد|السلام عليكم ورحمة الله وبركاته|أهلاً ومرحباً بكم|تحياتنا العطرة لسيادتكم}"
    openers = "{نود الاستفسار من جانبكم|نكتب إليكم لبحث إكانية التعاون|يسعدنا التواصل مع فريق العمل|نأمل الإفادة من جانبكم}"
    closers = "{مع فائق الاحترام والتقدير|دمتم برعاية الله وتوفيقه|تقبلوا خالص التحية|تحياتنا الحارة}"

    processed = text.replace("{GREETING}", greetings)
    processed = processed.replace("{OPENER}", openers)
    processed = processed.replace("{CLOSER}", closers)
    
    processed = processed.replace("{REF_NO}", ref_no)
    processed = processed.replace("{SENDER_NAME}", sender_name or "م. مصطفى رياض - مجموعة صمود")
    processed = processed.replace("{COMPANY}", company_name)
    processed = processed.replace("{DATE}", date_str)
    processed = processed.replace("{TIME}", time_str)
    processed = processed.replace("{DAY}", day_name)
    processed = processed.replace("{CITY}", city)
    processed = processed.replace("{SECTOR}", sector)
    
    return parse_spintax(processed)

if __name__ == "__main__":
    test_spintax = "نحن نقدم خدمات التوظيف المخصصة لـ {اسم_الشركة}."
    ctx = {"company_name": "مجموعة الرشيد للمقاولات", "language": "ar_fusha"}
    print("اختبار الافتتاحية الفريدة وتوليد الرسالة:")
    print(render_template(test_spintax, ctx))
