"""
مكتبة القوالب المسبقة والمجهزة لشركة صمود للتوظيف والتشغيل بالخارج
تتضمن بيانات 22 دولة عربية بمواعيد دوامها الرسمي، مع إخراج قوالب نقية 100% ومقروءة بدون تكرار في المحرر، وتطبيق الـ Spintax الديناميكي تلقائياً أثناء الإرسال.
"""

ARAB_COUNTRIES_DATA = [
    {"code": "SA", "name": "المملكة العربية السعودية", "flag": "🇸🇦", "timezone": "Asia/Riyadh", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "AE", "name": "الإمارات العربية المتحدة", "flag": "🇦🇪", "timezone": "Asia/Dubai", "utc": "UTC+4", "work_days": "الإثنين - الجمعة", "work_hours": "08:00 - 17:00"},
    {"code": "QA", "name": "دولة قطر", "flag": "🇶🇦", "timezone": "Asia/Qatar", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "KW", "name": "دولة الكويت", "flag": "🇰🇼", "timezone": "Asia/Kuwait", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "OM", "name": "سلطنة عمان", "flag": "🇴🇲", "timezone": "Asia/Muscat", "utc": "UTC+4", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "BH", "name": "مملكة البحرين", "flag": "🇧🇭", "timezone": "Asia/Bahrain", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "EG", "name": "جمهورية مصر العربية", "flag": "🇪🇬", "timezone": "Africa/Cairo", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "JO", "name": "المملكة الأردنية الهاشمية", "flag": "🇯🇴", "timezone": "Asia/Amman", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "IQ", "name": "جمهورية العراق", "flag": "🇮🇶", "timezone": "Asia/Baghdad", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "LB", "name": "الجمهورية اللبنانية", "flag": "🇱🇧", "timezone": "Asia/Beirut", "utc": "UTC+3", "work_days": "الإثنين - الجمعة", "work_hours": "08:00 - 17:00"},
    {"code": "LY", "name": "دولة ليبيا", "flag": "🇱🇾", "timezone": "Africa/Tripoli", "utc": "UTC+2", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "SD", "name": "جمهورية السودان", "flag": "🇸🇩", "timezone": "Africa/Khartoum", "utc": "UTC+2", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "MA", "name": "المملكة المغربية", "flag": "🇲🇦", "timezone": "Africa/Casablanca", "utc": "UTC+1", "work_days": "الإثنين - الجمعة", "work_hours": "08:00 - 17:00"},
    {"code": "DZ", "name": "الجمهورية الجزائرية", "flag": "🇩🇿", "timezone": "Africa/Algiers", "utc": "UTC+1", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "TN", "name": "الجمهورية التونسية", "flag": "🇹🇳", "timezone": "Africa/Tunis", "utc": "UTC+1", "work_days": "الإثنين - الجمعة", "work_hours": "08:00 - 17:00"},
    {"code": "YE", "name": "الجمهورية اليمنية", "flag": "🇾🇪", "timezone": "Asia/Aden", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "SY", "name": "الجمهورية العربية السورية", "flag": "🇸🇾", "timezone": "Asia/Damascus", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "PS", "name": "دولة فلسطين", "flag": "🇵🇸", "timezone": "Asia/Gaza", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "MR", "name": "الجمهورية الإسلامية الموريتانية", "flag": "🇲🇷", "timezone": "Africa/Nouakchott", "utc": "UTC+0", "work_days": "الإثنين - الجمعة", "work_hours": "08:00 - 17:00"},
    {"code": "SO", "name": "جمهورية الصومال", "flag": "🇸🇴", "timezone": "Africa/Mogadishu", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "DJ", "name": "جمهورية جيبوتي", "flag": "🇩🇯", "timezone": "Africa/Djibouti", "utc": "UTC+3", "work_days": "الأحد - الخميس", "work_hours": "08:00 - 17:00"},
    {"code": "KM", "name": "جزر القمر", "flag": "🇰🇲", "timezone": "Indian/Comoro", "utc": "UTC+3", "work_days": "الإثنين - الجمعة", "work_hours": "08:00 - 17:00"}
]

def synthesize_smart_template(
    sector: str = "المقاولات والتشييد",
    country_code: str = "SA",
    language: str = "العربية (فصحى)",
    active_vars: list = None
) -> dict:
    """المولّد الذكي للرسائل: يُخرج نصاً راقياً، أنيقاً، ونقياً 100% بدون تكرار أو أكواد Spintax مزعجة بالمحرر"""
    country_info = next((c for c in ARAB_COUNTRIES_DATA if c["code"] == country_code), ARAB_COUNTRIES_DATA[0])
    country_name = country_info["name"]
    country_flag = country_info["flag"]

    specialties = {
        "المقاولات والتشييد": "مدراء مشاريع تنفيذية، مهندسي موقع (مدني/كهرباء/ميكانيكا)، مشرفي جودة وسلامة HSE، ومساحين وعمالة حرفية ماهرة (حدادين، نجارين، بنائين)",
        "التشغيل والصيانة": "مهندسي صيانة مصانع ومرافق، فنيي تكييف وتبريد HVAC، كهربائيين، سباكين، وفنيي معدات ثقيلة وخبرات تشغيلية",
        "الرعاية الصحية": "أطباء استشاريين وأخصائيين في مختلف التخصصات، طاقم تمريض مؤهل، وأخصائيي مختبرات وأشعة وصيدلة",
        "تقنية المعلومات": "مهندسي برمجيات Full-Stack، مطوري Python/Node/React، مهندسي DevOps، وأخصائيي أمن معلومات وتطوير شبكات",
        "الفنادق والضيافة": "طهاة وطباخين (شرقي وغربي وحلويات)، مقدمي طعام ويترية، طاقم استقبال، ومدراء مطاعم وفنادق",
        "الأمن والحراسة": "مشرفي أمن وحراسات منشآت، حراس موقع، وأخصائيي سلامة وأمن صناعي",
        "التعليم والتدريب": "معلمين وأساتذة جامعيين في مختلف التخصصات العلمية والأدبية واللغات",
        "اللوجستيات والنقل": "مدراء لوجستيات، مشرفي حركة ونقل، وسائقي معدات وشاحنات ثقيلة"
    }

    spec_text = specialties.get(sector, "أفضل الكفاءات والخبرات التخصصية والكوادر المتميزة")

    if "English" in language:
        subject = f"Exclusive Manpower & Recruitment Proposal for {{اسم_الشركة}} in {country_name}"
        body = f"""Greetings to the Management Team at {{اسم_الشركة}} ({country_flag} {country_name}),

At **Samood Group for HR Services & Overseas Recruitment (License No. 1366 / 596)**, backed by over **25 years of excellence**, we specialize in supplying top-tier Egyptian talent tailored for leading organizations in {country_name}.

🎯 **Our Specialization in {sector}:**
👉 We supply verified, trade-tested candidates: {spec_text}.

✨ **Why Partner with Samood Group?**
🔹 **25+ Years Legacy**: Proven track record in Egyptian workforce supply.
🔹 **Rigorous Trade Testing**: Comprehensive technical and background screening prior to deployment.
🔹 **End-to-End Logistics**: Full support in visa processing and flight ticketing via *Ghaya Travel (Lic. 1539)*.
🔹 **100% Probation Guarantee**: Full performance guarantee during probation.

📁 Attached is our official Company Profile (PDF) for your review.

📲 **Direct WhatsApp Communication (Eng. Mostafa Riad - Samood Development):**
https://wa.me/201068158722

Best regards,
**Eng. Mostafa Riad - Samood Group Overseas Recruitment**
Email: info@somodeg.com | Website: www.somodeg.com"""

    elif "French" in language:
        subject = f"Offre de recrutement et partenariat pour {{اسم_الشركة}} - {country_name}"
        body = f"""Bonjour à l'équipe de direction de {{اسم_الشركة}} ({country_flag} {country_name}),

Le groupe **Samood Group pour le Recrutement International (Licence N° 1366 / 596)**, fort de plus de **25 ans d'expérience**, est spécialisé dans la fourniture de talents égyptiens qualifiés en {country_name}.

🎯 **Notre Spécialisation en {sector} :**
👉 Nous fournissons des candidats qualifiés: {spec_text}.

✨ **Nos Engagements et Merveilles :**
🔹 Plus de 25 ans d'excellence et d'éthique professionnelle.
🔹 Évaluation technique et tests professionnels rigoureux avant le départ.
🔹 Prise en charge logistique complète (Visas, Billets d'avion via Ghaya Travel Lic. 1539).
🔹 Période de garantie et d'essai garantie à 100%.

📁 Ci-joint notre Profil d'Entreprise (PDF).

📲 **Contact direct WhatsApp (Ing. Mostafa Riad - Développement Samood) :**
https://wa.me/201068158722

Cordialement,
**Ing. Mostafa Riad - Groupe Samood Recruitment**
Email: info@somodeg.com | Site Web: www.somodeg.com"""

    elif "خليجية" in language or "سعودية" in language:
        subject = f"عرض تعاون وتوفير كوادر {sector} لشركة {{اسم_الشركة}} في {country_name}"
        body = f"""تحية طيبة لمقام شركة {{اسم_الشركة}} الموقرة {country_flag} في {country_name}،

يسعدنا في **مجموعة شركات صمود وسهيل للتوظيف بالخارج (ترخيص رقم 1366 ورقم 596)** – إرث يمتد لأكثر من **25 عاماً من الثقة والتميز** – أن نعرض عليكم خدماتنا المتميزة في استقطاب وتوفير الكوادر والعمالة المصرية الكفء لمؤسستكم الموقرة.

🎯 **تخصصاتنا الفورية في قطاع ({sector}):**
👉 نوفر لكم: {spec_text}.

✨ **ليش تتعاملون مع مجموعة صمود؟**
🔹 **خبرة 25 عاماً**: إرث عريق ومصداقية لا تضاهى في استقدام العمالة والمهندسين.
🔹 **فحص واختبار دقيق**: تقييم ورش عمل واختبار مهارات موثق لكل كادر قبل السفر.
🔹 **دعم لوجستي متكامل (من الباب للباب)**: إنهاء التأشيرات والمقابلات وحجز الطيران عبر شركتنا الشقيقة *غاية للسياحة والطيران (ترخيص 1539)*.
🔹 **ضمان شامل**: فترة تجربة كاملة ومضمونة لكل العمالة الموردة.

📁 مرفق لكم ملف بروفايل الشركة (PDF) للاطلاع على سوابق أعمالنا وشراكاتنا.

📲 **للتواصل المباشر عبر الواتساب (م. مصطفى رياض - تطوير صمود):**
https://wa.me/201068158722

أطيب التحيات،
**م. مصطفى رياض - تطوير صمود**
إيميل: info@somodeg.com | الموقع: www.somodeg.com"""

    elif "مصرية" in language:
        subject = f"عرض خاص وتوفير عمالة {sector} لـ {{اسم_الشركة}} بـ {country_name}"
        body = f"""تحياتنا لسيادتكم في شركة {{اسم_الشركة}} {country_flag} في {country_name}،

معاكم **مجموعة شركات صمود وسهيل لتوفير والتحاق العمالة بالخارج (ترخيص 1366 و 596)**، خبرة أكتر من **25 سنة في السوق العربي**، وحابين نعرض على حضراتكم التعاون لتوفير العمالة المصرية المتميزة لمشاريعكم.

🎯 **تخصصاتنا الجاهزة في قطاع ({sector}):**
👉 بنقدر نوفر لحضراتكم: {spec_text}.

✨ **مميزات التعامل معانا:**
🔹 خبرة أكثر من 25 سنة واختبارات عمل موثقة قبل السفر.
🔹 سرعة إنهاء التأشيرات وحجز الطيران أوتوماتيكياً عن طريق شركتنا *غاية للسياحة وطيران (ترخيص 1539)*.
🔹 ضمان كامل وفترة تجربة لكل العمالة الموردة.

📁 مرفق الملف التعريفي للشركة (PDF) لسيادتكم.

📲 **للتواصل المباشر عبر الواتساب (م. مصطفى رياض - تطوير صمود):**
https://wa.me/201068158722

مع تحيات،
**م. مصطفى رياض - تطوير صمود**
إيميل: info@somodeg.com | الموقع: www.somodeg.com"""

    else: # فصحى
        subject = f"عرض تعاون توظيف وتوفير كوادر لشركة {{اسم_الشركة}} في {country_name}"
        body = f"""تحية طيبة وبعد لسيادتكم في شركة {{اسم_الشركة}} الموقرة {country_flag} في {country_name}،

يسعدنا في **مجموعة شركات صمود وسهيل للتوظيف بالخارج (ترخيص حكومي رقم 1366 ورقم 596)** – والتي تمتد خبرتها وأعمالها لأكثر من **25 عاماً من التميز والمصداقية** – أن نقدم لسيادتكم عرض تعاون مخصص لرفد منشأتكم بأفضل الكوادر المصرية المؤهلة.

🎯 **التخصصات المتوفرة لقطاع ({sector}):**
نغطي كافة احتياجاتكم من: {spec_text}.

✨ **أبرز مزايا التعاون مع مجموعة صمود:**
🔹 **إرث 25 عاماً من التميز**: مصداقية وقاعدة بيانات ضخمة من أصحاب الخبرات المصرية.
🔹 **اختبارات تقييم مهارية دقيقة**: فحص واختبار عملي للعمالة والمهندسين قبل السفر.
🔹 **حلول لوجستية شاملة**: إنهاء التأشيرات والمقابلات الطبية وحجوزات الطيران عبر شركتنا الشقيقة *غاية للسياحة والطيران (ترخيص 1539)*.
🔹 **ضمان وسرعة تنفيذ**: فترة تجربة كاملة وموثقة لضمان أعلى مستويات الكفاءة.

📁 مرفق مع الرسالة ملف بروفايل الشركة الشامل (PDF) للاطلاع.

📲 **للتواصل المباشر عبر الواتساب (م. مصطفى رياض - تطوير صمود):**
https://wa.me/201068158722

تقبلوا فائق الاحترام والتقدير،
**م. مصطفى رياض - تطوير مجموعة شركات صمود**
البريد الرسمي: info@somodeg.com | الموقع: www.somodeg.com"""

    return {
        "id": f"auto_{country_code}_{sector}",
        "title": f"🔥 قالب ذكي مخصص: {sector} ({country_name})",
        "sector": sector,
        "language": language,
        "subject": subject,
        "body": body
    }

BUILTIN_TEMPLATES = [
    {
        "id": "master_responsive_b2b",
        "title": "🔥 القالب الدعائي الفعال والمبهر (مجموعة صمود - ترخيص 1366)",
        "sector": "عام - كافة القطاعات",
        "language": "العربية (فصحى)",
        "subject": "عرض تعاون توظيف واستقدام كوادر لشركة {اسم_الشركة}",
        "body": """تحية طيبة وبعد لسيادتكم في شركة {اسم_الشركة}،

يسعدنا في **مجموعة شركات صمود وسهيل للتوظيف بالخارج (ترخيص رقم 1366 ورقم 596)** - بإرث يمتد لأكثر من **25 عاماً من التميز والخبرة** - تقديم عرض تعاون مخصص لتلبية كافة احتياجاتكم التوظيفية بسرعة فائقة وضمان تام.

✨ **لماذا تختار التعامل مع مجموعة صمود؟**
🔹 **توفير كافة التخصصات**: (مهندسين، مشرفين، فنيين، عمالة حرفية، طاقم طبي، وتكنولوجيا).
🔹 **فحص ودقة متناهية**: اختبارات مهنية وتقييم شامل لكل كادر قبل السفر.
🔹 **خدمات لوجستية كاملة**: إنهاء التأشيرات وحجوزات الطيران عبر *شركة غاية للسياحة والطيران (ترخيص 1539)*.
🔹 **ضمان شامل**: فترة تجربة كاملة وموثقة لضمان أعلى مستويات الأداء.

مرفق مع رسالتنا بروفايل الشركة الشامل (PDF) للاطلاع على سوابق أعمالنا وشركائنا.

📲 **للتواصل المباشر عبر الواتساب (م. مصطفى رياض - تطوير صمود):**
https://wa.me/201068158722

مع خالص التقدير والاحتساب،
**م. مصطفى رياض - تطوير مجموعة شركات صمود**
البريد الإلكتروني: info@somodeg.com
الموقع الرسمي: www.somodeg.com"""
    }
]
