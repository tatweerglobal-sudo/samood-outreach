import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database
import smtp_engine
import imaplib, ssl

accs = database.get_all_accounts()
for a in accs:
    email_addr = a["email"]
    pwd = a["password"]
    
    if "gmail.com" in email_addr.lower():
        imap_host = "imap.gmail.com"
    else:
        imap_host = a.get("imap_host") or "imap.hostinger.com"
        
    imap_port = 993
    print(f"\n--- Testing IMAP for {email_addr} on {imap_host}:{imap_port} ---")
    try:
        context = ssl.create_default_context()
        with imaplib.IMAP4_SSL(imap_host, imap_port, ssl_context=context) as M:
            M.login(email_addr, pwd)
            print(f"✅ LOGIN SUCCESSFUL for {email_addr} on {imap_host}!")
            res, folders = M.list()
            print(f"Folders count: {len(folders) if folders else 0}")
            
            # Check INBOX
            res_sel, data_sel = M.select("INBOX")
            print(f"INBOX status: {res_sel}, messages count: {data_sel[0] if data_sel else 0}")
            
            # Check UNSEEN
            typ, unseen_data = M.search(None, 'UNSEEN')
            print(f"UNSEEN in INBOX: {unseen_data}")
            
            # Check ALL messages in INBOX (last 5)
            typ_all, all_data = M.search(None, 'ALL')
            if typ_all == 'OK' and all_data[0]:
                msg_ids = all_data[0].split()
                print(f"Total messages in INBOX: {len(msg_ids)}. Last 3 IDs: {msg_ids[-3:]}")
    except Exception as e:
        print(f"❌ LOGIN FAILED for {email_addr}: {e}")
