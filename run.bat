@echo off
echo 🚀 راه‌اندازی ایجنت هوشمند دایرکت اینستاگرام
echo ===========================================
echo.

REM بررسی نصب Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python نصب نشده است
    echo لطفاً Python را از python.org دانلود کنید
    pause
    exit /b 1
)

REM ایجاد محیط مجازی اگر وجود ندارد
if not exist "venv" (
    echo 📦 ایجاد محیط مجازی...
    python -m venv venv
)

REM فعال‌سازی محیط مجازی
echo 🔧 فعال‌سازی محیط مجازی...
call venv\Scripts\activate.bat

REM نصب وابستگی‌ها
echo 📥 نصب وابستگی‌ها...
pip install -r requirements.txt

REM بررسی فایل .env
if not exist ".env" (
    echo ⚠️  فایل .env وجود ندارد. از .env.example کپی می‌شود...
    copy .env.example .env
    echo ⚠️  لطفاً کلید API خود را در فایل .env وارد کنید
)

REM ایجاد پوشه‌های مورد نیاز
if not exist "database" mkdir database

REM اجرای برنامه
echo ✅ همه چیز آماده است!
echo 🌐 سرور در حال اجرا است: http://localhost:5000
echo.

cd backend
python app.py

pause
