import re
import random
from typing import Dict, List

SPAM_TRIGGER_WORDS = [
    "مجاناً", "مجانا", "فرصة لا تعوض", "ربح سريع", "100% مضمون",
    "ضمان 100%", "اضغط هنا", "ارسل اموال", "ثراء", "عرض خاص جدا"
]

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
            return match.group(0) # الإبقاء على المتغيرات مثل {اسم_الشركة} كما هي دون تغيير
        
        new_text = re.sub(pattern, replace_match, text)
        if not match_found:
            break
        text = new_text
    return text

def render_template(
    template_spintax: str,
    context: Dict[str, str]
) -> str:
    """توليد النص النهائي بعد استبدال المتغيرات وفك الـ Spintax"""
    # 1. استبدال المتغيرات الديناميكية أولاً
    company_name = context.get("company_name") or "شركتكم الموقرة"
    contact_name = context.get("contact_name") or "السيد المسؤول"
    industry = context.get("industry") or "مجال عملكم"

    rendered = template_spintax.replace("{اسم_الشركة}", company_name)
    rendered = rendered.replace("{اسم_المسؤول}", contact_name)
    rendered = rendered.replace("{القطاع}", industry)
    rendered = rendered.replace("{المجال}", industry)
    
    # 2. فك الـ Spintax ثانياً
    rendered = parse_spintax(rendered)
    
    return rendered

def check_spam_keywords(text: str) -> List[str]:
    """فحص النص وإرجاع أي كلمات قد تثير شكوك فلاتر الـ Spam"""
    found_triggers = []
    for word in SPAM_TRIGGER_WORDS:
        if word in text:
            found_triggers.append(word)
    return found_triggers

if __name__ == "__main__":
    test_spintax = "{السلام عليكم|أهلاً بكم} شركة {اسم_الشركة}، نحن نقدم كوادر {متميزة|احترافية}."
    ctx = {"company_name": "الأمل للمقاولات"}
    print("اختبار توليد 3 نصوص مختلفة:")
    for _ in range(3):
        print("-", render_template(test_spintax, ctx))
    print("✅ محرك القوالب والـ Spintax جاهز ومكتمل!")
