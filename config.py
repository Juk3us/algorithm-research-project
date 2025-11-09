"""
تنظیمات سیستم معاملاتی اتوماتیک
Automated Trading System Configuration
"""

import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# ================== تنظیمات صرافی (Exchange Settings) ==================
EXCHANGE_NAME = 'kucoin'
API_KEY = os.getenv('API_KEY', 'YOUR_API_KEY')
API_SECRET = os.getenv('API_SECRET', 'YOUR_SECRET_KEY')
API_PASSWORD = os.getenv('API_PASSWORD', 'YOUR_PASSWORD')

# ================== تنظیمات بازار (Market Settings) ==================
MARKET_SYMBOL = 'BTC/USDT'  # نماد معاملاتی
CHART_TIMEFRAME = '30m'      # تایم فریم: 30 دقیقه
BASE_CURRENCY = 'USDT'       # ارز پایه

# ================== تنظیمات زمانی (Timezone Settings) ==================
TIMEZONE = 'Asia/Tehran'  # منطقه زمانی تهران (GMT+3:30)

# ================== سشن‌های معاملاتی (Trading Sessions) ==================
# همه زمان‌ها بر اساس GMT+3 است
TRADING_SESSIONS = {
    'tokyo': {
        'name': 'Tokyo (Asia)',
        'open': '01:00',
        'close': '09:30',
        'gmt_offset': 3
    },
    'london': {
        'name': 'London (Europe)',
        'open': '07:00',
        'close': '15:30',
        'gmt_offset': 3
    },
    'newyork': {
        'name': 'New York (America)',
        'open': '18:00',
        'close': '02:30',  # روز بعد
        'gmt_offset': 3
    }
}

# ================== همپوشانی سشن‌ها (Session Overlaps) ==================
# این زمان‌ها کلید اصلی تصمیم‌گیری هستند
SESSION_OVERLAPS = {
    'newyork_tokyo': {
        'name': 'NewYork-Tokyo Overlap',
        'start': '01:00',
        'end': '02:30',
        'priority': 2,  # اولویت متوسط
        'allow_trading': True
    },
    'tokyo_london': {
        'name': 'Tokyo-London Overlap',
        'start': '07:00',
        'end': '09:30',
        'priority': 3,  # اولویت بالا
        'allow_trading': True
    },
    'rest_time': {
        'name': 'Rest Time (No Trading)',
        'start': '15:30',
        'end': '18:00',
        'priority': 0,  # بدون اولویت
        'allow_trading': False  # زمان استراحت - معامله ممنوع
    }
}

# ================== مدیریت ریسک (Risk Management) ==================
# حداکثر درصد سرمایه قابل ریسک در هر معامله
MAX_TRADE_RISK = 0.05  # 5%

# حداکثر درصد کل سرمایه برای استاپ لاس
STOP_LOSS_RISK = 0.03  # 3%

# محدودیت‌های ضرر
DAILY_STOP_LOSS = 0.07    # 7% ضرر روزانه
WEEKLY_STOP_LOSS = 0.10   # 10% ضرر هفتگی
MONTHLY_STOP_LOSS = 0.15  # 15% ضرر ماهانه

# نسبت ریسک به ریوارد
RISK_REWARD_RATIO = 2.0  # برای هر 1 واحد ریسک، 2 واحد سود

# حداقل موجودی برای معامله
MIN_BALANCE = 10.0  # حداقل 10 USDT

# ================== تنظیمات استراتژی (Strategy Settings) ==================
# نوع استراتژی
STRATEGY_TYPE = 'session_swing_retouch'  # استراتژی بر اساس تاچ سوئینگ‌های سشن قبلی

# حداقل تعداد کندل برای تحلیل
MIN_CANDLES = 100  # افزایش برای شناسایی بهتر سوئینگ‌ها

# حداقل تغییر قیمت برای ورود به معامله (به درصد)
MIN_PRICE_CHANGE = 0.3  # 0.3%

# تعداد کندل برای تحلیل روند
TREND_ANALYSIS_PERIOD = 10  # آخرین 10 کندل

# ================== تنظیمات شناسایی سوئینگ (Swing Detection) ==================
# تعداد کندل‌های گذشته برای شناسایی سوئینگ
SWING_LOOKBACK = 50  # 50 کندل گذشته

# حداقل تعداد کندل بین دو سوئینگ
MIN_SWING_DISTANCE = 5  # حداقل 5 کندل فاصله

# درصد تلرانس برای تاچ سوئینگ (به درصد)
SWING_TOUCH_TOLERANCE = 0.3  # 0.3% تلرانس

# حداکثر فاصله زمانی سوئینگ (تعداد کندل)
MAX_SWING_AGE = 100  # سوئینگ‌های بیشتر از 100 کندل قدیمی نادیده گرفته می‌شوند

# حداقل قدرت سوئینگ (تفاوت با کندل‌های همسایه به درصد)
MIN_SWING_STRENGTH = 0.2  # 0.2%

# تعداد کندل‌های چپ و راست برای تأیید سوئینگ
SWING_CONFIRMATION_CANDLES = 2  # 2 کندل چپ و راست

# ================== قوانین معاملاتی بر اساس سوئینگ ==================
# اصل اول: تمام سوئینگ‌ها یک بار دیگر تاچ می‌شوند
SWING_RETOUCH_PRINCIPLE = True

# معامله در سوئینگ های Lower Low
TRADE_ON_LOWER_LOWS = True  # خرید در تاچ Lower Low

# معامله در سوئینگ های Higher High
TRADE_ON_HIGHER_HIGHS = True  # فروش در تاچ Higher High

# استفاده از ATR برای محاسبه استاپ لاس
USE_ATR_STOP_LOSS = True
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5

# ================== تنظیمات لاگ (Logging Settings) ==================
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = 'trading_bot.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ================== تنظیمات حالت آزمایشی (Test Mode) ==================
TEST_MODE = True  # فعال‌سازی حالت آزمایشی (بدون معامله واقعی)
PAPER_TRADING = True  # معامله کاغذی
INITIAL_PAPER_BALANCE = 1000.0  # موجودی اولیه برای معامله کاغذی

# ================== تنظیمات پیشرفته (Advanced Settings) ==================
# فاصله زمانی بین بررسی‌ها (به ثانیه)
CHECK_INTERVAL = 60  # هر 60 ثانیه یک‌بار

# حداکثر تعداد معاملات باز همزمان
MAX_OPEN_POSITIONS = 3

# استفاده از trailing stop
USE_TRAILING_STOP = True
TRAILING_STOP_PERCENTAGE = 0.02  # 2%

# حداکثر تعداد تلاش مجدد در صورت خطا
MAX_RETRIES = 3

# زمان انتظار بین تلاش‌های مجدد (به ثانیه)
RETRY_DELAY = 5

# ================== تنظیمات اعلان (Notification Settings) ==================
ENABLE_NOTIFICATIONS = False
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# ================== تنظیمات دیتابیس (Database Settings) ==================
USE_DATABASE = True
DATABASE_PATH = 'trading_data.db'

# ================== توابع کمکی (Helper Functions) ==================
def validate_config():
    """بررسی اعتبار تنظیمات"""
    errors = []

    if API_KEY == 'YOUR_API_KEY':
        errors.append("API_KEY تنظیم نشده است")

    if API_SECRET == 'YOUR_SECRET_KEY':
        errors.append("API_SECRET تنظیم نشده است")

    if API_PASSWORD == 'YOUR_PASSWORD':
        errors.append("API_PASSWORD تنظیم نشده است")

    if MAX_TRADE_RISK <= 0 or MAX_TRADE_RISK > 0.1:
        errors.append("MAX_TRADE_RISK باید بین 0 و 0.1 باشد")

    if RISK_REWARD_RATIO < 1:
        errors.append("RISK_REWARD_RATIO باید حداقل 1 باشد")

    return errors

def print_config():
    """چاپ تنظیمات فعلی"""
    print("=" * 60)
    print("تنظیمات سیستم معاملاتی".center(60))
    print("=" * 60)
    print(f"صرافی: {EXCHANGE_NAME}")
    print(f"نماد: {MARKET_SYMBOL}")
    print(f"تایم فریم: {CHART_TIMEFRAME}")
    print(f"منطقه زمانی: {TIMEZONE}")
    print(f"حالت آزمایشی: {'بله' if TEST_MODE else 'خیر'}")
    print(f"حداکثر ریسک هر معامله: {MAX_TRADE_RISK * 100}%")
    print(f"استاپ لاس روزانه: {DAILY_STOP_LOSS * 100}%")
    print(f"نسبت ریسک/ریوارد: {RISK_REWARD_RATIO}")
    print("=" * 60)

    errors = validate_config()
    if errors:
        print("\n⚠️  خطاهای تنظیمات:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ همه تنظیمات معتبر هستند")
    print("=" * 60)

if __name__ == "__main__":
    print_config()
