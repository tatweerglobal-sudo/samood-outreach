import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database
import flask_app

print("=== INSPECTING DB ACCOUNTS & WARMUP LOGS ===")
accs = database.get_all_accounts()
print(f"Total accounts in DB: {len(accs)}")
for a in accs:
    print(f" - ID: {a['id']}, Email: {a['email']}, Active: {a['is_active']}, Limit: {a['daily_limit']}")

print("\n=== TRIGGERING WARMUP CYCLE ===")
with flask_app.app.test_client() as client:
    res = client.post("/api/warmup/trigger-cycle")
    print("Response JSON:", res.get_json())

print("\n=== WARMUP LOGS IN DB ===")
logs = database.get_warmup_logs(limit=20)
print(f"Total logs recorded: {len(logs)}")
for l in logs:
    print(f" - ID: {l['id']} | Sender: {l['account_email']} -> Target: {l['target_email']} | Subject: {l['subject']} | Action: {l['imap_action']} | Status: {l['status']}")
