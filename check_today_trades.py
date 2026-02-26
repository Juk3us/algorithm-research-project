#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اسکریپت بررسی معاملات امروز
این اسکریپت وضعیت فعلی بازار و معاملات احتمالی امروز را نشان می‌دهد
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import config

class TodayTradeChecker:
    def __init__(self, symbol='AUD/USD'):
        self.symbol = symbol
        self.gmt_plus_3 = pytz.timezone('Europe/Moscow')  # GMT+3

    def get_current_session(self, timestamp: datetime) -> str:
        """تشخیص سشن فعلی"""
        hour = timestamp.hour
        minute = timestamp.minute
        time_in_minutes = hour * 60 + minute

        # تبدیل زمان‌های سشن به دقیقه (GMT+3)
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

    def is_in_overlap(self, timestamp: datetime) -> tuple:
        """بررسی اینکه آیا در overlap هستیم"""
        hour = timestamp.hour
        minute = timestamp.minute
        time_in_minutes = hour * 60 + minute

        # Tokyo-London overlap: 07:00 - 09:30
        if 420 <= time_in_minutes <= 570:
            return True, 'tokyo-london'

        # NewYork-Tokyo overlap: 01:00 - 02:30
        if 60 <= time_in_minutes <= 150:
            return True, 'newyork-tokyo'

        return False, None

    def generate_sample_data(self, hours=24):
        """تولید داده‌های نمونه برای آزمایش"""
        now = datetime.now(self.gmt_plus_3)
        start_time = now - timedelta(hours=hours)

        # تولید داده‌های ساعتی
        timestamps = pd.date_range(start=start_time, end=now, freq='1H')

        # قیمت شروع تصادفی
        base_price = np.random.uniform(0.64, 0.66)

        data = []
        for ts in timestamps:
            # نوسانات تصادفی
            change = np.random.uniform(-0.005, 0.005)
            base_price = base_price * (1 + change)

            # کندل
            open_price = base_price
            high = open_price * (1 + np.random.uniform(0, 0.003))
            low = open_price * (1 - np.random.uniform(0, 0.003))
            close = np.random.uniform(low, high)

            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close
            })

        return pd.DataFrame(data)

    def detect_swing_highs_lows(self, df: pd.DataFrame, lookback=5):
        """تشخیص سوئینگ های‌ها و لوها"""
        swings = {
            'highs': [],
            'lows': []
        }

        for i in range(lookback, len(df) - lookback):
            # Swing High
            if df.iloc[i]['high'] == df.iloc[i-lookback:i+lookback+1]['high'].max():
                swings['highs'].append({
                    'price': df.iloc[i]['high'],
                    'time': df.iloc[i]['timestamp'],
                    'index': i
                })

            # Swing Low
            if df.iloc[i]['low'] == df.iloc[i-lookback:i+lookback+1]['low'].min():
                swings['lows'].append({
                    'price': df.iloc[i]['low'],
                    'time': df.iloc[i]['timestamp'],
                    'index': i
                })

        return swings

    def analyze_today(self):
        """تحلیل معاملات امروز"""
        print("=" * 80)
        print("🔍 تحلیل معاملات امروز - AUD/USD")
        print("=" * 80)

        # زمان فعلی
        now = datetime.now(self.gmt_plus_3)
        print(f"\n⏰ زمان فعلی (GMT+3): {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # سشن فعلی
        current_session = self.get_current_session(now)
        if current_session:
            print(f"📊 سشن فعلی: {current_session.upper()}")
        else:
            print("⚠️  در خارج از ساعات معاملاتی اصلی هستیم")

        # بررسی overlap
        in_overlap, overlap_type = self.is_in_overlap(now)
        if in_overlap:
            print(f"🔄 در Overlap: {overlap_type}")
            print("   → در حال تشخیص روند - هنوز معامله باز نمی‌شود")
        else:
            print("✅ خارج از Overlap - می‌توان معامله باز کرد")

        print("\n" + "-" * 80)
        print("📈 تحلیل 24 ساعت گذشته:")
        print("-" * 80)

        # تولید داده‌های نمونه
        df = self.generate_sample_data(hours=24)

        # قیمت فعلی
        current_price = df.iloc[-1]['close']
        price_24h_ago = df.iloc[0]['close']
        change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100

        print(f"\n💰 قیمت فعلی: ${current_price:.5f}")
        print(f"📊 تغییر 24 ساعته: {change_24h:+.2f}%")

        # تحلیل سشن‌های امروز
        print("\n" + "-" * 80)
        print("📋 سشن‌های امروز:")
        print("-" * 80)

        # محاسبه سشن‌های امروز
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        sessions_today = []

        # سشن توکیو
        tokyo_start = today_start.replace(hour=1, minute=0)
        tokyo_end = today_start.replace(hour=9, minute=30)
        if tokyo_start <= now:
            tokyo_data = df[(df['timestamp'] >= tokyo_start) & (df['timestamp'] <= tokyo_end)]
            if len(tokyo_data) > 0:
                sessions_today.append({
                    'name': 'TOKYO',
                    'start': tokyo_start,
                    'end': tokyo_end,
                    'completed': now > tokyo_end,
                    'data': tokyo_data
                })

        # سشن لندن
        london_start = today_start.replace(hour=7, minute=0)
        london_end = today_start.replace(hour=15, minute=30)
        if london_start <= now:
            london_data = df[(df['timestamp'] >= london_start) & (df['timestamp'] <= london_end)]
            if len(london_data) > 0:
                sessions_today.append({
                    'name': 'LONDON',
                    'start': london_start,
                    'end': london_end,
                    'completed': now > london_end,
                    'data': london_data
                })

        # سشن نیویورک (ممکنه از دیشب شروع شده باشه)
        ny_start = (today_start - timedelta(days=1)).replace(hour=18, minute=0)
        ny_end = today_start.replace(hour=2, minute=30)
        if now >= ny_start:
            ny_data = df[(df['timestamp'] >= ny_start) & (df['timestamp'] <= ny_end)]
            if len(ny_data) > 0:
                sessions_today.append({
                    'name': 'NEWYORK',
                    'start': ny_start,
                    'end': ny_end,
                    'completed': now > ny_end,
                    'data': ny_data
                })

        # نمایش سشن‌ها
        trades_count = 0
        for session in sessions_today:
            status = "✅ تکمیل شده" if session['completed'] else "🔄 در حال اجرا"
            print(f"\n{session['name']}: {status}")
            print(f"   زمان: {session['start'].strftime('%H:%M')} - {session['end'].strftime('%H:%M')}")

            if len(session['data']) > 0:
                session_high = session['data']['high'].max()
                session_low = session['data']['low'].min()
                session_range = ((session_high - session_low) / session_low) * 100

                print(f"   دامنه: ${session_low:.5f} - ${session_high:.5f} ({session_range:.2f}%)")

                # تشخیص سوئینگ‌ها
                swings = self.detect_swing_highs_lows(session['data'], lookback=2)
                print(f"   Swing Highs: {len(swings['highs'])} | Swing Lows: {len(swings['lows'])}")

                # اگر سشن تکمیل شده و overlap بعدش هم تموم شده
                # یعنی احتمالا یه سیگنال داشتیم
                if session['completed']:
                    trades_count += 1

        print("\n" + "=" * 80)
        print(f"📊 خلاصه: تعداد معاملات احتمالی امروز: {trades_count}")
        print("=" * 80)

        print("\n⚠️  توجه: این تحلیل بر اساس داده‌های شبیه‌سازی شده است.")
        print("   برای نتایج دقیق، نیاز به اتصال به یک broker فارکس (مثل OANDA) است.")

        return trades_count

if __name__ == '__main__':
    checker = TodayTradeChecker()
    checker.analyze_today()
