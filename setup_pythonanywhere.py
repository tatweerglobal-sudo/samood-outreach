import os
import sys
import time
import requests

USERNAME = "mostafa2510"
API_TOKEN = "a4b165c946ca51110ff2e116ef40af862e683ec2"
DOMAIN = f"{USERNAME}.pythonanywhere.com"
BASE_URL = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}"

HEADERS = {
    "Authorization": f"Token {API_TOKEN}"
}

def upload_file_to_pa(local_path: str, remote_rel_path: str) -> bool:
    remote_full_path = f"/home/{USERNAME}/samood-outreach/{remote_rel_path}".replace("\\", "/")
    url = f"{BASE_URL}/files/path{remote_full_path}"
    
    with open(local_path, "rb") as f:
        content = f.read()
        
    res = requests.post(url, headers=HEADERS, files={"content": content})
    return res.status_code in [200, 201]

def setup_pythonanywhere_cloud():
    print("=" * 65)
    print(" 🚀 تفعيل محرك Flask المضمون 100% على PythonAnywhere... 🚀")
    print("=" * 65)

    project_dir = os.path.dirname(__file__)
    exclude = ["samood_data.db", "__pycache__", ".git", "uploads", "samood_project.zip"]

    # 1. رفع كافة الملفات
    count = 0
    for root, dirs, files in os.walk(project_dir):
        if any(x in root for x in exclude):
            continue
        for file in files:
            if file in exclude or file.endswith(".db") or file.endswith(".pyc"):
                continue
            local_path = os.path.join(root, file)
            rel_path = os.path.relpath(local_path, project_dir).replace("\\", "/")
            if upload_file_to_pa(local_path, rel_path):
                count += 1
    print(f" -> تم تحديث {count} ملف سحابي!")

    # 2. ضبط ملف WSGI المعتمد رسمياً بـ Flask
    wsgi_content = f"""import sys
import os

path = '/home/{USERNAME}/samood-outreach'
if path not in sys.path:
    sys.path.insert(0, path)

os.chdir(path)

from flask_app import app as application
"""
    wsgi_path = f"/var/www/{USERNAME}_pythonanywhere_com_wsgi.py"
    requests.post(
        f"{BASE_URL}/files/path{wsgi_path}",
        headers=HEADERS,
        files={"content": wsgi_content.encode("utf-8")}
    )
    print(" -> تم إعداد ملف WSGI المضمون رسمياً من PythonAnywhere!")

    # 3. إعادة تحميل السيرفر لتفعيل التغييرات 24/7
    res_reload = requests.post(f"{BASE_URL}/webapps/{DOMAIN}/reload/", headers=HEADERS)
    if res_reload.status_code in [200, 201]:
        print("\n🎉🎉🎉 تم تشغيل وإطلاق سيرفر صمود السحابي المباشر بنجاح 100%! 🎉🎉🎉")
        print(f"الرابط المباشر الأونلاين للشركة: https://{DOMAIN}")
    else:
        print(f" -> نتيجة Reload: {res_reload.status_code}")

if __name__ == "__main__":
    setup_pythonanywhere_cloud()
