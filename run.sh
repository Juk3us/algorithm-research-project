#!/bin/bash

echo "🚀 راه‌اندازی ایجنت هوشمند دایرکت اینستاگرام"
echo "==========================================="

# بررسی نصب Python
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 نصب نشده است"
    exit 1
fi

# ایجاد محیط مجازی اگر وجود ندارد
if [ ! -d "venv" ]; then
    echo "📦 ایجاد محیط مجازی..."
    python3 -m venv venv
fi

# فعال‌سازی محیط مجازی
echo "🔧 فعال‌سازی محیط مجازی..."
source venv/bin/activate

# نصب وابستگی‌ها
echo "📥 نصب وابستگی‌ها..."
pip install -r requirements.txt

# بررسی فایل .env
if [ ! -f ".env" ]; then
    echo "⚠️  فایل .env وجود ندارد. از .env.example کپی می‌شود..."
    cp .env.example .env
    echo "⚠️  لطفاً کلید API خود را در فایل .env وارد کنید"
fi

# ایجاد پوشه‌های مورد نیاز
mkdir -p database

# اجرای برنامه
echo "✅ همه چیز آماده است!"
echo "🌐 سرور در حال اجرا است: http://localhost:5000"
echo ""

cd backend && python app.py
