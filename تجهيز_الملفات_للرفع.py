import os
import zipfile

def create_project_zip():
    project_dir = os.path.dirname(__file__)
    zip_filename = os.path.join(project_dir, "samood_project.zip")
    
    exclude_files = ["samood_project.zip", "samood_data.db", "__pycache__"]
    
    print("=" * 65)
    print("      📦 جاري تجميع وتجهيز ملفات مشروع صمود في ملف مضغوط... 📦")
    print("=" * 65)
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            if "__pycache__" in root or "uploads" in root:
                continue
            for file in files:
                if file in exclude_files or file.endswith(".db") or file.endswith(".pyc"):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, project_dir)
                zipf.write(file_path, arcname)
                print(f" -> إضافة: {arcname}")
                
    print(f"\n🎉 تم تجميع الملف بنجاح في: {zip_filename}")
    print("يمكنك سحب هذا الملف أو فكه ورفعه مباشرة على GitHub!")

if __name__ == "__main__":
    create_project_zip()
