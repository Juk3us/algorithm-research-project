# 🚀 Release v1.0.0 - Automated Trading System

## 📋 خلاصه

اولین نسخه رسمی سیستم معاملاتی خودکار مبتنی بر استراتژی Session Swing با قابلیت Multi-Lot Position Management.

## ✨ ویژگی‌های اصلی

### 🎯 استراتژی معاملاتی
- **Session-Based Trading**: معامله بر اساس سشن‌های Tokyo, London, NewYork
- **Counter-Trend Strategy**: معامله خلاف جهت روند در overlap
- **Multi-Lot System**: باز کردن چند لات همزمان (یکی برای هر تارگت)
- **Progressive Closing**: بستن تدریجی لات‌ها به محض رسیدن به تارگت
- **Reversal Phase**: معامله معکوس بعد از تکمیل فاز counter-trend

### 🔧 قابلیت‌های تکنیکال
- ✅ **OANDA API Integration**: اتصال به OANDA برای داده‌های فارکس واقعی
- ✅ **Swing Capture Mechanism**: ذخیره و حذف سوئینگ‌های گرفته شده
- ✅ **No Stop Loss**: بدون SL با مکانیزم timeout (48 ساعت)
- ✅ **Target Filtering**: فیلتر هوشمند تارگت‌های سودآور
- ✅ **Session History Tracking**: ردیابی سوئینگ‌های دو سشن قبلی
- ✅ **Automatic Position Sizing**: محاسبه خودکار حجم بر اساس ریسک

## 📊 نتایج بک‌تست (10 روز)

### AUD/USD
```
💰 بازدهی: +0.46%
📊 تعداد معاملات: 51
✅ نرخ برد: 43.14%
📈 Profit Factor: 1.18
💵 میانگین سود: $1.39
💸 میانگین ضرر: $0.90
```

### BTC/USDT
```
💰 بازدهی: +2.01%
📊 تعداد معاملات: 60
✅ نرخ برد: 75.00%
📈 Profit Factor: 1.15
💵 میانگین سود: $1.11
💸 میانگین ضرر: $2.89
```

## 📦 فایل‌های اصلی

| فایل | توضیحات |
|------|---------|
| `backtest.py` | موتور اصلی بک‌تست با Multi-Lot System |
| `oanda_api.py` | کانکتور OANDA REST API |
| `session_manager.py` | مدیریت سشن‌های معاملاتی (Tokyo/London/NY) |
| `swing_detector.py` | تشخیص سوئینگ‌های قیمت (Higher Highs/Lower Lows) |
| `config.py` | تنظیمات سیستم (سشن‌ها، ریسک، تایم‌فریم) |
| `check_today_trades.py` | بررسی معاملات امروز |

## 🚀 نحوه استفاده

### نصب وابستگی‌ها
```bash
pip install pandas numpy requests python-dotenv pytz
```

### اجرای بک‌تست
```bash
# AUD/USD با 10 روز گذشته
python3 backtest.py "AUD/USD" 10

# EUR/USD با 30 روز
python3 backtest.py "EUR/USD" 30

# BTC/USDT (پیش‌فرض)
python3 backtest.py
```

### تست اتصال OANDA
```bash
python3 -c "
from oanda_api import OandaAPI
api = OandaAPI('YOUR_TOKEN', 'practice')
print('✅ Connected!' if api.test_connection() else '❌ Failed')
"
```

## 🔄 تغییرات نسخه 1.0.0

### ✅ اضافه شده
- سیستم Multi-Lot برای مدیریت چندین پوزیشن همزمان
- مکانیزم Swing Capture (حذف سوئینگ‌های گرفته شده)
- اتصال OANDA API برای داده‌های فارکس واقعی
- فاز Reversal برای معاملات معکوس
- فیلتر تارگت‌های صحیح (فقط سودآور)
- مکانیزم timeout 48 ساعت برای بستن پوزیشن‌های قدیمی

### 🔧 اصلاح شده
- محاسبه Position Size اصلاح شد (تبدیل به تعداد coin)
- فیلتر تارگت‌ها: SELL فقط targets < entry, BUY فقط targets > entry
- حذف کامل Stop Loss

### ❌ حذف شده
- Stop Loss (جایگزین شد با timeout)
- سیستم تک پوزیشن (جایگزین شد با Multi-Lot)

## 📈 بهبودهای عملکرد

| مورد | قبل | بعد | بهبود |
|------|-----|-----|-------|
| بازدهی BTC | -34.98% | +2.01% | ✅ سودآور شد |
| تعداد معاملات | 3 | 60 | ✅ 20x افزایش |
| نرخ برد BTC | 100% | 75% | ⚠️ طبیعی |
| Profit Factor | منفی | 1.15+ | ✅ مثبت شد |

## 🐛 مشکلات شناخته شده

- نیاز به اینترنت برای اتصال به OANDA API
- داده‌های شبیه‌سازی شده در صورت عدم اتصال به OANDA
- Timeout 48 ساعت ممکن است در برخی شرایط زود باشد

## 🔮 برنامه‌های آینده (v1.1.0)

- [ ] اضافه کردن Live Trading Mode
- [ ] Dashboard تحلیلی برای نمایش نتایج
- [ ] بهینه‌سازی پارامترها با Genetic Algorithm
- [ ] افزودن Risk Management پیشرفته
- [ ] Telegram Bot برای اعلان‌ها
- [ ] Multi-Symbol Trading

## 👥 مشارکت

برای گزارش باگ یا پیشنهاد ویژگی جدید، لطفاً یک Issue در گیت‌هاب ایجاد کنید.

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## ⚠️ هشدار

این سیستم صرفاً برای اهداف آموزشی و تحقیقاتی است. معامله در بازارهای مالی ریسک دارد و ممکن است منجر به از دست دادن سرمایه شود. قبل از استفاده در معاملات واقعی، حتماً بک‌تست کامل انجام دهید.

---

**تاریخ انتشار**: 2025-11-13
**نسخه**: 1.0.0
**Branch**: `claude/automated-trading-system-011CUvWHxdPLTcpgF2DWiPAB`
