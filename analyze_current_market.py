#!/usr/bin/env python3
"""
تحلیل وضعیت فعلی بازار AUD/USD
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import pytz
import config
from swing_detector import SessionSwingManager


def get_current_session(timestamp: datetime) -> str:
    """تشخیص سشن فعلی"""
    hour = timestamp.hour
    minute = timestamp.minute
    time_in_minutes = hour * 60 + minute

    # تبدیل زمان‌های سشن به دقیقه
    sessions = {
        'tokyo': (60, 570),      # 01:00 - 09:30
        'london': (420, 930),    # 07:00 - 15:30
        'newyork': (1080, 150)   # 18:00 - 02:30 (روز بعد)
    }

    # بررسی نیویورک (که از شب قبل شروع میشه)
    if time_in_minutes >= 1080 or time_in_minutes <= 150:
        return 'newyork'
    # توکیو
    elif 60 <= time_in_minutes <= 570:
        return 'tokyo'
    # لندن
    elif 420 <= time_in_minutes <= 930:
        return 'london'
    else:
        return None


def analyze_market():
    """تحلیل بازار فعلی"""
    print("\n" + "="*80)
    print("تحلیل وضعیت فعلی بازار AUD/USD".center(80))
    print("="*80)

    # اتصال به صرافی
    exchange = None
    for exchange_class in [ccxt.binance, ccxt.bybit, ccxt.okx]:
        try:
            exchange = exchange_class({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            exchange.load_markets()
            print(f"✅ اتصال به {exchange.name} برقرار شد")
            break
        except Exception as e:
            print(f"⚠️  خطا در اتصال به {exchange_class.__name__}: {e}")
            continue

    if not exchange:
        print("❌ نمی‌توانم به هیچ صرافی متصل شوم")
        print("\n⚠️  توجه: برای AUD/USD نیاز به broker فارکس داریم، نه صرافی کریپتو")
        print("   پیشنهاد: از داده‌های یک بروکر فارکس مانند OANDA یا یک سرویس داده استفاده کنید")
        return

    # دریافت داده‌های 3 روز گذشته (برای شناسایی سوئینگ‌ها)
    try:
        symbol = 'AUD/USD'
        timeframe = '30m'
        since = int((datetime.now() - timedelta(days=3)).timestamp() * 1000)

        print(f"\n📥 دریافت داده‌های {symbol}...")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since)

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # تبدیل به GMT+3
        df.index = df.index.tz_localize('UTC').tz_convert('Etc/GMT-3')

        # آخرین قیمت
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]

        print(f"\n💰 قیمت فعلی: ${current_price:.5f}")
        print(f"🕐 زمان: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (GMT+3)")

        # تشخیص سشن فعلی
        current_session = get_current_session(current_time)
        if current_session:
            print(f"📍 سشن فعلی: {current_session.upper()}")
        else:
            print(f"⏸️  در حال حاضر در هیچ سشنی نیستیم (استراحت)")
            return

        # جداسازی داده‌ها بر اساس سشن
        session_data = {'tokyo': [], 'london': [], 'newyork': []}

        for idx, candle in df.iterrows():
            session = get_current_session(idx)
            if session:
                session_data[session].append(candle)

        # تحلیل سوئینگ‌ها
        swing_manager = SessionSwingManager()

        print("\n" + "="*80)
        print("تحلیل سوئینگ‌های سشن‌ها".center(80))
        print("="*80)

        for session_name in ['tokyo', 'london', 'newyork']:
            if session_data[session_name]:
                session_df = pd.DataFrame(session_data[session_name])
                swing_manager.update_session_swings(session_name, session_df)

                swings = swing_manager.sessions[session_name]
                print(f"\n📊 سشن {session_name.upper()}:")
                print(f"   Higher Highs: {len(swings['highs'])} عدد")
                if swings['highs']:
                    for i, swing in enumerate(swings['highs'][:5], 1):
                        print(f"      {i}. ${swing['price']:.5f} (قدرت: {swing['strength']:.2f}%)")

                print(f"   Lower Lows: {len(swings['lows'])} عدد")
                if swings['lows']:
                    for i, swing in enumerate(swings['lows'][:5], 1):
                        print(f"      {i}. ${swing['price']:.5f} (قدرت: {swing['strength']:.2f}%)")

        # تحلیل overlap توکیو-لندن
        print("\n" + "="*80)
        print("تحلیل Overlap توکیو-لندن".center(80))
        print("="*80)

        # پیدا کردن overlap (07:00 - 09:30)
        overlap_data = df[(df.index.hour >= 7) & (df.index.hour < 10)]

        if len(overlap_data) > 0:
            # آخرین overlap
            last_overlap = overlap_data.tail(20)  # حدود 10 ساعت

            if len(last_overlap) > 1:
                start_price = last_overlap['close'].iloc[0]
                end_price = last_overlap['close'].iloc[-1]
                change_pct = ((end_price - start_price) / start_price) * 100

                if abs(change_pct) >= config.MIN_PRICE_CHANGE:
                    trend = 'bullish' if change_pct > 0 else 'bearish'
                    print(f"\n   روند در overlap: {trend.upper()} ({change_pct:.2f}%)")
                    print(f"   قیمت شروع overlap: ${start_price:.5f}")
                    print(f"   قیمت پایان overlap: ${end_price:.5f}")

                    # سیگنال counter-trend
                    signal = 'sell' if trend == 'bullish' else 'buy'
                    print(f"\n   → سیگنال معامله (counter-trend): {signal.upper()}")
                else:
                    print(f"\n   روند در overlap: NEUTRAL ({change_pct:.2f}%) - خیلی ضعیف")
        else:
            print("\n   ⚠️  داده overlap کافی نیست")

        print("\n" + "="*80)

    except Exception as e:
        print(f"❌ خطا: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_market()
