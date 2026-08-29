import os
import time
import json
import asyncio
import threading
import datetime
import platform
import psutil
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, Request, Depends
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

import database
import smtp_engine
import excel_processor
import template_engine
import auth

app = FastAPI(title="Samood Email Outreach Platform", version="2026.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

database.init_db()

# --- محرك تشغيل الحملات بالخلفية ---

class CampaignManager:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.current_index: int = 0
        self.status: str = "STOPPED"
        self.current_log: str = "البرنامج متوقف ورئيسي بانتظار بدء الحملة"
        self.selected_template_id: Optional[int] = None
        self.next_send_time: Optional[float] = None
        self.circuit_breaker = smtp_engine.CircuitBreaker()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.subscribers: List[asyncio.Queue] = []

    def set_records(self, records: List[Dict[str, Any]]):
        with self._lock:
            self.records = records
            self.current_index = 0

    def broadcast_event(self, event_data: Dict[str, Any]):
        data_str = f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
        loop = asyncio.get_event_loop() if asyncio._get_running_loop() else None
        for q in self.subscribers[:]:
            try:
                if loop and loop.is_running():
                    loop.call_soon_threadsafe(q.put_nowait, data_str)
                else:
                    q.put_nowait(data_str)
            except Exception:
                pass

    def run_loop(self):
        account_rotator_idx = 0
        while self.status == "RUNNING":
            with self._lock:
                if self.current_index >= len(self.records):
                    self.status = "STOPPED"
                    database.set_campaign_status("STOPPED")
                    self.current_log = "🎉 تم الانتهاء من إرسال كافة رسائل الحملة بنجاح!"
                    self.broadcast_event({"type": "FINISHED", "message": self.current_log})
                    break

                record = self.records[self.current_index]

            settings = database.get_settings()
            
            if settings.get("working_hours_only"):
                now_hour = datetime.datetime.now().hour
                start_h = settings.get("work_start_hour", 8)
                end_h = settings.get("work_end_hour", 17)
                if not (start_h <= now_hour < end_h):
                    self.current_log = f"⏳ خارج ساعات العمل الرسمية ({start_h}:00 إلى {end_h}:00). الانتظار مؤقتاً..."
                    self.broadcast_event({"type": "WAITING_WORK_HOURS", "message": self.current_log})
                    time.sleep(60)
                    continue

            active_accounts = database.get_active_accounts()
            if not active_accounts:
                self.status = "PAUSED"
                database.set_campaign_status("PAUSED")
                self.current_log = "⚠️ تم إيقاف الحملة: لا توجد حسابات بريد فعالة أو تجاوزت الحسابات الحد اليومي!"
                self.broadcast_event({"type": "PAUSED_NO_ACCOUNTS", "message": self.current_log})
                break

            account = active_accounts[account_rotator_idx % len(active_accounts)]
            account_rotator_idx += 1

            templates = database.get_templates()
            if not templates:
                self.status = "STOPPED"
                self.current_log = "⚠️ خطأ: لا يوجد قالب رسائل متاح!"
                self.broadcast_event({"type": "ERROR", "message": self.current_log})
                break
            
            template = next((t for t in templates if t["id"] == self.selected_template_id), templates[0])

            subject = template_engine.render_template(template["subject_spintax"], record)
            body = template_engine.render_template(template["body_spintax"], record)
            attachment = template.get("attachment_path")

            email = record["email"]
            self.current_log = f"🚀 جاري الإرسال إلى {record.get('company_name')} ({email}) عبر {account['email']}..."
            self.broadcast_event({"type": "SENDING", "email": email, "company": record.get("company_name"), "log": self.current_log})

            success, error_msg = smtp_engine.send_single_email(
                account=account,
                recipient_email=email,
                subject=subject,
                body_text=body,
                attachment_path=attachment
            )

            if success:
                database.record_sent_log(
                    recipient_email=email,
                    company_name=record.get("company_name"),
                    contact_name=record.get("contact_name"),
                    industry=record.get("industry"),
                    account_email=account["email"],
                    subject_used=subject,
                    status="SENT"
                )
                self.circuit_breaker.record(True)
                self.current_log = f"✅ تم الإرسال بنجاح إلى {email}"
            else:
                database.record_sent_log(
                    recipient_email=email,
                    company_name=record.get("company_name"),
                    contact_name=record.get("contact_name"),
                    industry=record.get("industry"),
                    account_email=account["email"],
                    subject_used=subject,
                    status="FAILED",
                    error_details=error_msg
                )
                self.circuit_breaker.record(False)
                self.current_log = f"❌ فشل الإرسال إلى {email}: {error_msg}"

            if self.circuit_breaker.is_tripped():
                self.status = "PAUSED"
                database.set_campaign_status("PAUSED")
                self.current_log = "🚨 تم تفعيل قاطع التيار الطارئ: ارتفاع نسبة الارتداد عن الحد الآمن (1.5%)! تم إيقاف الحملة لحماية البريد."
                self.broadcast_event({"type": "CIRCUIT_BREAKER_TRIPPED", "message": self.current_log})
                break

            with self._lock:
                self.current_index += 1

            min_d = settings.get("delay_min_seconds", 45)
            max_d = settings.get("delay_max_seconds", 90)
            delay = smtp_engine.calculate_gaussian_delay(min_d, max_d)
            self.next_send_time = time.time() + delay

            self.broadcast_event({
                "type": "PROGRESS",
                "current": self.current_index,
                "total": len(self.records),
                "log": self.current_log,
                "next_delay_seconds": round(delay, 1)
            })

            start_wait = time.time()
            while time.time() - start_wait < delay:
                if self.status != "RUNNING":
                    break
                time.sleep(1)

    def start(self, template_id: Optional[int] = None):
        if not self.records:
            raise ValueError("لم يتم رفع ملف Excel أو تصفية بيانات بعد!")
        
        self.selected_template_id = template_id
        self.status = "RUNNING"
        database.set_campaign_status("RUNNING")
        
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self.run_loop, daemon=True)
            self._thread.start()

    def pause(self):
        self.status = "PAUSED"
        database.set_campaign_status("PAUSED")
        self.current_log = "⏸️ تم إيقاف الحملة مؤقتاً بطلب من المستخدم"
        self.broadcast_event({"type": "PAUSED", "message": self.current_log})

    def resume(self):
        if self.records and self.current_index < len(self.records):
            self.status = "RUNNING"
            database.set_campaign_status("RUNNING")
            if not self._thread or not self._thread.is_alive():
                self._thread = threading.Thread(target=self.run_loop, daemon=True)
                self._thread.start()

    def stop(self):
        self.status = "STOPPED"
        database.set_campaign_status("STOPPED")
        self.current_log = "🛑 تم إنهاء الحملة كلياً"
        self.broadcast_event({"type": "STOPPED", "message": self.current_log})

campaign = CampaignManager()

# --- الـ Endpoints والمصادقة الأونلاين ---

@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = database.verify_admin_login(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور غير صحيحة")
    token = auth.create_session(user["username"], user["display_name"])
    return {
        "success": True,
        "token": token,
        "user": {"username": user["username"], "display_name": user["display_name"]}
    }

@app.post("/api/logout")
def logout(request: Request):
    token = request.cookies.get("samood_session")
    if token:
        auth.destroy_session(token)
    return {"success": True, "message": "تم تسجيل الخروج بنجاح"}

@app.post("/api/change-password")
def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    admin: Dict[str, Any] = Depends(auth.get_current_admin)
):
    user = database.verify_admin_login(admin["username"], old_password)
    if not user:
        raise HTTPException(status_code=400, detail="كلمة المرور القديمة غير صحيحة")
    database.change_admin_password(admin["username"], new_password)
    return {"success": True, "message": "تم تغيير كلمة المرور بنجاح!"}

@app.get("/api/server-info")
def get_server_info(admin: Dict[str, Any] = Depends(auth.get_current_admin)):
    return {
        "os": platform.system() + " " + platform.release(),
        "python_version": platform.python_version(),
        "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
        "ram_usage_percent": psutil.virtual_memory().percent,
        "admin_user": admin["display_name"],
        "server_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/api/status")
def get_campaign_status():
    stats = database.get_stats()
    active_accounts = database.get_active_accounts()
    return {
        "status": campaign.status,
        "current_index": campaign.current_index,
        "total_records": len(campaign.records),
        "log": campaign.current_log,
        "sent_count": stats["sent_count"],
        "failed_count": stats["failed_count"],
        "unsub_count": stats["unsub_count"],
        "active_accounts_count": len(active_accounts),
        "next_send_time": campaign.next_send_time
    }

@app.post("/api/upload-excel")
async def upload_excel(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())

    try:
        valid_rows, stats = excel_processor.parse_excel_file(file_location)
        campaign.set_records(valid_rows)
        return {
            "success": True,
            "message": f"تم تحليل الملف بنجاح! تم استخراج {len(valid_rows)} شركة جاهزة للإرسال.",
            "stats": stats,
            "sample_rows": valid_rows[:50]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/accounts")
def list_accounts():
    return database.get_all_accounts()

@app.post("/api/accounts")
def add_account(
    email: str = Form(...),
    password: str = Form(...),
    smtp_host: str = Form(...),
    smtp_port: int = Form(...),
    use_ssl: bool = Form(True),
    sender_name: str = Form(...),
    daily_limit: int = Form(45)
):
    ok, msg = smtp_engine.test_smtp_connection(smtp_host, smtp_port, use_ssl, email, password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    database.add_smtp_account(email, password, smtp_host, smtp_port, use_ssl, sender_name, daily_limit)
    return {"success": True, "message": "تم إضافة واختبار بريد الإلكتروني بنجاح!"}

@app.delete("/api/accounts/{account_id}")
def remove_account(account_id: int):
    database.delete_account(account_id)
    return {"success": True, "message": "تم حذف الحساب"}

@app.post("/api/test-email")
def test_email(
    smtp_host: str = Form(...),
    smtp_port: int = Form(...),
    use_ssl: bool = Form(True),
    email: str = Form(...),
    password: str = Form(...),
    sender_name: str = Form(...),
    target_email: str = Form(...)
):
    acc = {
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "use_ssl": use_ssl,
        "email": email,
        "password": password,
        "sender_name": sender_name,
        "id": 0
    }
    subj = "اختبار بريد تجريبي - شركة صمود"
    body = "السلام عليكم، هذه رسالة تجريبية لتأكيد صحة الربط مع خادم البريد لشركة صمود."
    ok, msg = smtp_engine.send_single_email(acc, target_email, subj, body)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": f"تم إرسال البريد التجريبي بنجاح إلى {target_email}"}

@app.get("/api/templates")
def list_templates():
    return database.get_templates()

@app.post("/api/templates")
async def save_template_endpoint(
    title: str = Form(...),
    industry: str = Form("عام"),
    subject_spintax: str = Form(...),
    body_spintax: str = Form(...),
    template_id: Optional[int] = Form(None),
    attachment: Optional[UploadFile] = File(None)
):
    att_path = None
    if attachment:
        att_path = os.path.join(UPLOAD_DIR, attachment.filename)
        with open(att_path, "wb") as f:
            f.write(await attachment.read())

    spam_triggers = template_engine.check_spam_keywords(subject_spintax + " " + body_spintax)
    
    database.save_template(title, industry, subject_spintax, body_spintax, att_path, template_id)
    return {
        "success": True,
        "message": "تم حفظ القالب بنجاح!",
        "spam_warnings": spam_triggers
    }

@app.get("/api/settings")
def get_settings():
    return database.get_settings()

@app.post("/api/settings")
def update_settings(
    delay_min_seconds: int = Form(45),
    delay_max_seconds: int = Form(90),
    hourly_cap_per_account: int = Form(20),
    working_hours_only: bool = Form(True),
    work_start_hour: int = Form(8),
    work_end_hour: int = Form(17),
    warmup_mode: bool = Form(False)
):
    data = {
        "delay_min_seconds": delay_min_seconds,
        "delay_max_seconds": delay_max_seconds,
        "hourly_cap_per_account": hourly_cap_per_account,
        "working_hours_only": working_hours_only,
        "work_start_hour": work_start_hour,
        "work_end_hour": work_end_hour,
        "warmup_mode": warmup_mode
    }
    database.update_settings(data)
    return {"success": True, "message": "تم حفظ الإعدادات بنجاح"}

@app.post("/api/campaign/start")
def start_campaign(template_id: Optional[int] = Form(None)):
    try:
        campaign.start(template_id)
        return {"success": True, "message": "تم بدء الحملة بنجاح!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/campaign/pause")
def pause_campaign():
    campaign.pause()
    return {"success": True, "message": "تم إيقاف الحملة مؤقتاً"}

@app.post("/api/campaign/resume")
def resume_campaign():
    campaign.resume()
    return {"success": True, "message": "تم استئناف الحملة"}

@app.post("/api/campaign/stop")
def stop_campaign():
    campaign.stop()
    return {"success": True, "message": "تم إنهاء الحملة"}

@app.get("/api/export-logs")
def export_logs():
    conn = database.get_connection()
    df = pd.read_sql_query("SELECT * FROM sent_logs ORDER BY id DESC;", conn)
    conn.close()
    
    export_path = os.path.join(UPLOAD_DIR, "تقرير_إرسال_صمود.xlsx")
    df.to_excel(export_path, index=False)
    return FileResponse(export_path, filename="تقرير_إرسال_صمود.xlsx")

@app.get("/unsub")
@app.get("/api/unsub")
def handle_unsubscribe(email: str):
    database.add_unsubscribe(email)
    return Response(content="<h2>تم إلغاء مراسلتكم بنجاح. شكراً لوقتكم.</h2>", media_type="text/html")

@app.get("/api/events")
async def events_stream(request: Request):
    async def event_generator():
        q = asyncio.Queue()
        campaign.subscribers.append(q)
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield data
        finally:
            if q in campaign.subscribers:
                campaign.subscribers.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
