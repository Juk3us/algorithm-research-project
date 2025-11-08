#!/usr/bin/env python3
"""
نقطه ورود اصلی ربات معاملاتی
Main Entry Point for Trading Bot
"""

import sys
import argparse
from datetime import datetime
import config
from trading_bot import TradingBot
from session_manager import SessionManager
from risk_manager import RiskManager


def print_banner():
    """چاپ بنر ربات"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║          🤖 ربات معاملاتی اتوماتیک بر اساس سشن‌های جهانی          ║
    ║        Automated Trading Bot Based on Global Sessions           ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_config():
    """بررسی تنظیمات"""
    print("\n🔍 بررسی تنظیمات...")
    print("-" * 70)

    errors = config.validate_config()

    if errors:
        print("\n❌ خطاهای تنظیمات:")
        for error in errors:
            print(f"  • {error}")
        print("\n💡 راهنما:")
        print("  1. فایل .env را ایجاد کنید")
        print("  2. کلیدهای API صرافی را در آن قرار دهید:")
        print("     API_KEY=your_api_key")
        print("     API_SECRET=your_secret_key")
        print("     API_PASSWORD=your_password")
        print("-" * 70)
        return False

    print("✓ تنظیمات معتبر است")
    print("-" * 70)
    return True


def show_status():
    """نمایش وضعیت فعلی"""
    print("\n📊 وضعیت فعلی سیستم")
    print("=" * 70)

    # نمایش تنظیمات
    config.print_config()

    # نمایش سشن‌ها
    sm = SessionManager()
    sm.print_status()


def run_bot():
    """اجرای ربات"""
    try:
        # بررسی تنظیمات
        if not check_config():
            if config.TEST_MODE:
                print("\n⚠️  اجرا در حالت آزمایشی ادامه می‌یابد...")
            else:
                print("\n❌ لطفاً تنظیمات را اصلاح کنید و دوباره اجرا کنید")
                sys.exit(1)

        # ایجاد و اجرای ربات
        bot = TradingBot()
        bot.run()

    except KeyboardInterrupt:
        print("\n\n🛑 توقف ربات توسط کاربر")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {str(e)}")
        sys.exit(1)


def test_components():
    """تست اجزای سیستم"""
    print("\n🧪 تست اجزای سیستم")
    print("=" * 70)

    # تست Session Manager
    print("\n1️⃣  تست مدیریت سشن‌ها...")
    sm = SessionManager()
    sm.print_status()

    # تست Risk Manager
    print("\n2️⃣  تست مدیریت ریسک...")
    rm = RiskManager()
    rm.update_balance(1000.0)
    rm.print_statistics()

    # تست Trading Bot
    print("\n3️⃣  تست ربات معاملاتی...")
    bot = TradingBot()
    print("✓ ربات با موفقیت ساخته شد")

    # اجرای یک چرخه تست
    print("\n4️⃣  اجرای یک چرخه تست...")
    bot.run_once()

    print("\n" + "=" * 70)
    print("✓ همه تست‌ها با موفقیت انجام شد")
    print("=" * 70)


def main():
    """تابع اصلی"""
    print_banner()

    # پارس کردن آرگومان‌های خط فرمان
    parser = argparse.ArgumentParser(
        description='ربات معاملاتی اتوماتیک بر اساس سشن‌های جهانی'
    )

    parser.add_argument(
        '--mode',
        choices=['run', 'status', 'test'],
        default='run',
        help='حالت اجرا: run (اجرای ربات), status (نمایش وضعیت), test (تست اجزا)'
    )

    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='فعال‌سازی حالت آزمایشی (بدون معامله واقعی)'
    )

    parser.add_argument(
        '--config',
        help='مسیر فایل تنظیمات سفارشی'
    )

    args = parser.parse_args()

    # تنظیم حالت آزمایشی
    if args.test_mode:
        config.TEST_MODE = True
        config.PAPER_TRADING = True
        print("⚠️  حالت آزمایشی فعال شد")

    # اجرای دستور مورد نظر
    if args.mode == 'status':
        show_status()

    elif args.mode == 'test':
        test_components()

    elif args.mode == 'run':
        # نمایش اطلاعات اولیه
        print(f"\n📅 تاریخ و زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌍 منطقه زمانی: {config.TIMEZONE}")
        print(f"💱 نماد معاملاتی: {config.MARKET_SYMBOL}")
        print(f"⏱️  تایم فریم: {config.CHART_TIMEFRAME}")
        print(f"🔧 حالت: {'آزمایشی' if config.TEST_MODE else 'واقعی'}")
        print()

        # اجرای ربات
        run_bot()


if __name__ == "__main__":
    main()
