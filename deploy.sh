#!/bin/bash
# سكريبت نشر وتثبيت برنامج صمود على السيرفر السحابي أونلاين (Hostinger VPS / DigitalOcean / Hetzner)

echo "===================================================================="
echo "      🚀 نشر وتشغيل منظومة صمود على السيرفر السحابي الأونلاين 🚀"
echo "===================================================================="

# تثبيت Docker إذا لم يكن موجوداً
if ! command -v docker &> /dev/null
then
    echo "[1/3] جاري تثبيت Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# تثبيت Docker Compose إذا لم يكن موجوداً
if ! command -v docker-compose &> /dev/null
then
    echo "[2/3] جاري تثبيت Docker Compose..."
    sudo apt-get update && sudo apt-get install -y docker-compose
fi

echo "[3/3] جاري بناء وبدء وتشغيل الحاوية السحابية..."
docker-compose down
docker-compose build
docker-compose up -d

echo ""
echo "===================================================================="
echo "🎉 تم تشغيل برنامج صمود على السيرفر السحابي أونلاين بنجاح!"
echo "يمكنك الدخول إلى لوحة التحكم عبر عنوان السيرفر: http://YOUR_SERVER_IP:8000"
echo "===================================================================="
