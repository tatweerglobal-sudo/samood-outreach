import os
import subprocess
import sys

def main():
    print("=" * 65)
    print("      🚀 رفع وتحديث كود برنامج صمود تلقائياً على GitHub 🚀")
    print("=" * 65)
    print()

    repo_url = input("ادخل رابط مستودع GitHub الخاص بك (Repository URL): ").strip()

    if not repo_url:
        print("⚠️ لم يتم أدخال رابط! يرجى إعادة التشغيل وأدخال الرابط.")
        input("\nاضغط Enter للخروج...")
        sys.exit(1)

    print("\n[1/4] جاري إعداد وتجهيز مستودع Git المحلي...")
    subprocess.run(["git", "init"], check=False)
    subprocess.run(["git", "add", "."], check=False)
    subprocess.run(["git", "commit", "-m", "إطلاق برنامج صمود للتسويق الإلكتروني 2026"], check=False)

    print("[2/4] جاري ضبط الفرع الرئيسي (main)...")
    subprocess.run(["git", "branch", "-M", "main"], check=False)

    print("[3/4] جاري ربط المستودع بالرابط:")
    print(f" -> {repo_url}")
    subprocess.run(["git", "remote", "remove", "origin"], check=False)
    subprocess.run(["git", "remote", "add", "origin", repo_url], check=False)

    print("[4/4] جاري الرفع على GitHub... (قد يطلب تسجيل الدخول بحسابك في GitHub)")
    res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"])

    if res.returncode == 0:
        print("\n🎉 تم الرفع بنجاح 100% على GitHub!")
    else:
        print("\n⚠️ حدث تنبيه أثناء الرفع. تأكد من صحة الرابط وأنك مسجل الدخول في GitHub.")

    input("\nاضغط Enter لإغلاق هذه الشاشة...")

if __name__ == "__main__":
    main()
