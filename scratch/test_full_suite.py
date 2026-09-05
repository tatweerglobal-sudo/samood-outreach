import sys
import os
import requests
import json

BASE_URL = "https://mostafa2510.pythonanywhere.com"

def log_pass(msg):
    print(f"✅ [PASSED]: {msg}")

def log_fail(msg):
    print(f"❌ [FAILED]: {msg}")

def run_tests():
    print("==========================================================")
    print("🚀 بدء الفحص الشامل والاختبار التلقائي لجميع أنظمة صمود (Zero Errors Test)...")
    print("==========================================================")
    
    passed_count = 0
    failed_count = 0

    # Test 1: API Server Status
    try:
        res = requests.get(f"{BASE_URL}/api/status")
        if res.status_code == 200 and res.json().get("status") == "success":
            log_pass("سيرفر API والحالة العامة (Status Check)")
            passed_count += 1
        else:
            log_fail(f"سيرفر API: {res.status_code}")
            failed_count += 1
    except Exception as e:
        log_fail(f"سيرفر API: {str(e)}")
        failed_count += 1

    # Test 2: Arab Countries API (22 Countries)
    try:
        res = requests.get(f"{BASE_URL}/api/countries")
        data = res.json()
        if res.status_code == 200 and len(data.get("countries", [])) == 22:
            log_pass("بيانات الـ 22 دولة عربية بتوقيتاتها الرسمية (Arab Countries Data)")
            passed_count += 1
        else:
            log_fail("بيانات الـ 22 دولة عربية")
            failed_count += 1
    except Exception as e:
        log_fail(f"بيانات الـ 22 دولة: {str(e)}")
        failed_count += 1

    # Test 3: Template Synthesis Engine & 8 Anti-Spam Switches
    try:
        payload = {
            "sector": "المقاولات والتشييد",
            "country_code": "SA",
            "language": "العربية (فصحى)",
            "active_vars": ["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8"]
        }
        res = requests.post(f"{BASE_URL}/api/templates/synthesize", json=payload)
        data = res.json()
        if res.status_code == 200 and "template" in data and "body" in data["template"]:
            log_pass("مولد القوالب الذكي والـ 8 متغيرات لمكافحة الحظر (Synthesize Engine)")
            passed_count += 1
        else:
            log_fail("مولد القوالب الذكي والـ 8 متغيرات")
            failed_count += 1
    except Exception as e:
        log_fail(f"مولد القوالب: {str(e)}")
        failed_count += 1

    # Test 4: Excel Upload & Ultra Column Detector
    try:
        csv_content = "ID,Country,Company_Name,Primary_Email,Secondary_Email,Sector\nDZ-001,Algeria,شركة الجزائر,test_p@gmail.com,test_s@gmail.com,مقاولات\n"
        files = {'file': ('test_suite.csv', csv_content.encode('utf-8'), 'text/csv')}
        res = requests.post(f"{BASE_URL}/api/excel/upload", files=files)
        if res.status_code == 200:
            data = res.json()
            if data.get("valid_count", 0) >= 1:
                log_pass("محرك قراءة الإكسيل واستخراج البريد الأساسي والثانوي (Excel Engine)")
                passed_count += 1
            else:
                log_fail(f"محرك قراءة الإكسيل: {data.get('message')}")
                failed_count += 1
        else:
            log_fail(f"محرك قراءة الإكسيل HTTP {res.status_code}: {res.text[:200]}")
            failed_count += 1
    except Exception as e:
        log_fail(f"محرك الإكسيل: {str(e)}")
        failed_count += 1

    # Test 5: Excel Repository Library API (GET /api/excel/files)
    try:
        res = requests.get(f"{BASE_URL}/api/excel/files")
        data = res.json()
        if res.status_code == 200 and len(data.get("files", [])) >= 1:
            log_pass("مكتبة ملفات الإكسيل الدائمة والحفظ السحابي (Cloud Excel Library)")
            passed_count += 1
        else:
            log_fail("مكتبة ملفات الإكسيل الدائمة")
            failed_count += 1
    except Exception as e:
        log_fail(f"مكتبة الإكسيل: {str(e)}")
        failed_count += 1

    # Test 6: 1-Click Launch Wizard API
    try:
        res = requests.post(f"{BASE_URL}/api/campaign/launch-wizard")
        if res.status_code in [200, 400]:
            data = res.json()
            log_pass(f"مركز الإطلاق الفوري بنقرة واحدة وتفتيش الجاهزية (1-Click Launch Wizard): {data.get('message', 'OK')}")
            passed_count += 1
        else:
            log_fail(f"مركز الإطلاق HTTP {res.status_code}: {res.text[:200]}")
            failed_count += 1
    except Exception as e:
        log_fail(f"مركز الإطلاق: {str(e)}")
        failed_count += 1

    # Test 7: Official Proposal Builder API
    try:
        payload = {"company_name": "شركة المقاولات الوطنية", "sector": "المقاولات والتشييد", "country": "المملكة العربية السعودية"}
        res = requests.post(f"{BASE_URL}/api/proposal/generate", json=payload)
        data = res.json()
        if res.status_code == 200 and "proposal_html" in data:
            log_pass("مولد عروض التوظيف الرسمية والمقترحات المطبوعة (Proposal Builder)")
            passed_count += 1
        else:
            log_fail("مولد عروض التوظيف الرسمية")
            failed_count += 1
    except Exception as e:
        log_fail(f"مولد المقترحات: {str(e)}")
        failed_count += 1

    # Test 8: Settings Management & 6 Master Switches
    try:
        payload = {
            "target_country": "SA",
            "delay_min_seconds": 45,
            "delay_max_seconds": 90,
            "hourly_cap_per_account": 20,
            "golden_hour_enabled": True,
            "hot_lead_alert_enabled": True,
            "alert_whatsapp_number": "201068158722",
            "anti_trap_shield_enabled": True,
            "double_impact_enabled": True,
            "auto_load_balancing_enabled": True
        }
        res = requests.post(f"{BASE_URL}/api/settings", json=payload)
        data = res.json()
        if res.status_code == 200 and data.get("status") == "success":
            log_pass("لوحة التحكم بالمفاتيح الـ 6 والخوارزميات المتقدمة (Master Settings API)")
            passed_count += 1
        else:
            log_fail("لوحة التحكم بالمفاتيح الـ 6")
            failed_count += 1
    except Exception as e:
        log_fail(f"لوحة التحكم بالمفاتيح: {str(e)}")
        failed_count += 1

    # Test 9: CRM Deal Pipeline Board API
    try:
        res = requests.get(f"{BASE_URL}/api/crm/deals")
        data = res.json()
        if res.status_code == 200 and "deals" in data:
            log_pass("لوحة تتبع وإدارة الصفقات والعملاء (CRM Deal Pipeline API)")
            passed_count += 1
        else:
            log_fail("لوحة إدارة الصفقات CRM")
            failed_count += 1
    except Exception as e:
        log_fail(f"لوحة إدارة الصفقات: {str(e)}")
        failed_count += 1

    # Test 11: Domain Email Extractor Tool API
    try:
        res = requests.post(f"{BASE_URL}/api/tools/extract-emails", json={"domain": "sonatrach.dz"})
        data = res.json()
        if res.status_code == 200 and "extracted_emails" in data:
            log_pass("مستخرج إيميلات الشركات والـ HR الآلي من الدومينات (Domain Email Extractor)")
            passed_count += 1
        else:
            log_fail("مستخرج إيميلات الشركات من الدومين")
            failed_count += 1
    except Exception as e:
        log_fail(f"مستخرج الإيميلات: {str(e)}")
        failed_count += 1

    # Test 12: Interactive Recruitment Form API
    try:
        res = requests.get(f"{BASE_URL}/api/tools/recruitment-form")
        if res.status_code == 200 and "مجموعة شركات صمود" in res.text:
            log_pass("نموذج واستمارة طلب الكوادر والعمالة التفاعلية (Interactive Recruitment Request Form)")
            passed_count += 1
        else:
            log_fail("نموذج طلب الكوادر التفاعلي")
            failed_count += 1
    except Exception as e:
        log_fail(f"نموذج طلب الكوادر: {str(e)}")
        failed_count += 1

    # Test 13: Executive PDF/HTML Audit Report API
    try:
        res = requests.get(f"{BASE_URL}/api/reports/executive-summary")
        data = res.json()
        if res.status_code == 200 and "report_html" in data:
            log_pass("التقرير التنفيذي الرسمي المطبوع لأداء المنظومة (Executive Audit Report PDF)")
            passed_count += 1
        else:
            log_fail("التقرير التنفيذي المطبوع")
            failed_count += 1
    except Exception as e:
        log_fail(f"التقرير التنفيذي: {str(e)}")
        failed_count += 1

    # Test 14: AI Icebreaker Generator API
    try:
        res = requests.post(f"{BASE_URL}/api/tools/ai-icebreaker", json={"company_name": "شركة صمود", "sector": "مقاولات", "country": "SA"})
        data = res.json()
        if res.status_code == 200 and len(data.get("icebreakers", [])) >= 1:
            log_pass("مولد المقدمات المخصصة بالذكاء الاصطناعي (AI Icebreaker Generator)")
            passed_count += 1
        else:
            log_fail("مولد المقدمات المخصصة بالذكاء الاصطناعي")
            failed_count += 1
    except Exception as e:
        log_fail(f"مولد المقدمات الذكية: {str(e)}")
        failed_count += 1

    # Test 15: Enterprise Live Analytics Dashboard API
    try:
        res = requests.get(f"{BASE_URL}/api/analytics/dashboard")
        data = res.json()
        if res.status_code == 200 and "inbox_delivery_rate" in data:
            log_pass("لوحة التحليلات والإحصائيات الحية المتقدمة (Enterprise Live Analytics Dashboard)")
            passed_count += 1
        else:
            log_fail("لوحة التحليلات والإحصائيات الحية")
            failed_count += 1
    except Exception as e:
        log_fail(f"لوحة التحليلات: {str(e)}")
        failed_count += 1

    # Test 16: WhatsApp Bulk Double Impact Campaign API
    try:
        res = requests.get(f"{BASE_URL}/api/tools/whatsapp-campaign")
        data = res.json()
        if res.status_code == 200 and "links" in data:
            log_pass("مولد حملات الواتساب المزدوجة المباشرة بنقرة واحدة (Double-Impact WhatsApp Generator)")
            passed_count += 1
        else:
            log_fail("مولد حملات الواتساب المزدوجة")
            failed_count += 1
    except Exception as e:
        log_fail(f"مولد الواتساب المزدوج: {str(e)}")
        failed_count += 1

    # Test 17: Warmup Accounts Status API
    try:
        res = requests.get(f"{BASE_URL}/api/warmup/status")
        data = res.json()
        if res.status_code == 200 and "warmup_status" in data:
            log_pass("محرك جدول الحسابات وخطة التسخين الزمنية (Warmup Status API)")
            passed_count += 1
        else:
            log_fail("محرك جدول الحسابات وخطة التسخين")
            failed_count += 1
    except Exception as e:
        log_fail(f"محرك جدول الحسابات والتسخين: {str(e)}")
        failed_count += 1

    # Test 18: Warmup Threads API
    try:
        res = requests.get(f"{BASE_URL}/api/warmup/threads")
        data = res.json()
        if res.status_code == 200 and "threads" in data:
            log_pass("محرك عارض المحادثات والسلاسل النشطة (Warmup Active Threads API)")
            passed_count += 1
        else:
            log_fail("محرك عارض المحادثات والسلاسل النشطة")
            failed_count += 1
    except Exception as e:
        log_fail(f"محرك السلاسل النشطة: {str(e)}")
        failed_count += 1

    # Test 19: 4-Turn B2B Dialogue Simulator API
    try:
        res = requests.get(f"{BASE_URL}/api/warmup/synthesize-4turns")
        data = res.json()
        if res.status_code == 200 and len(data.get("turns", [])) == 4:
            log_pass("محاكي ومولد المحادثات التفاعلية الـ 4 مراحل (4-Turn B2B Simulator API)")
            passed_count += 1
        else:
            log_fail("محاكي المحادثات الـ 4 مراحل")
            failed_count += 1
    except Exception as e:
        log_fail(f"محاكي الـ 4 مراحل: {str(e)}")
        failed_count += 1

    print("==========================================================")
    print(f"📊 نتيجة الفحص النهائي: {passed_count} اختبار نجح | {failed_count} اختبار فشل")
    print("==========================================================")
    if failed_count == 0:
        print("🎉🎉🎉 تبارك الله! النتيجة 100% نسبة الأخطاء = 0%! النظام جاهز تماماً للتشغيل!")

if __name__ == "__main__":
    run_tests()
