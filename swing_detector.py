"""
شناسایی و مدیریت سوئینگ‌های هر سشن معاملاتی
Session-Based Swing Detection and Management
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import os

import config


class SessionSwingManager:
    """مدیریت سوئینگ‌های هر سشن معاملاتی"""

    def __init__(self, persistence_file: str = 'session_swings.json'):
        """
        مقداردهی اولیه

        Args:
            persistence_file: فایل ذخیره سوئینگ‌ها
        """
        self.persistence_file = persistence_file

        # جدول سوئینگ‌های هر سشن
        # format: {'session_name': {'highs': [...], 'lows': [...]}}
        self.session_swings = {
            'tokyo': {'highs': [], 'lows': []},
            'london': {'highs': [], 'lows': []},
            'newyork': {'highs': [], 'lows': []}
        }

        # بارگذاری از فایل
        self.load_swings()

    def save_swings(self):
        """ذخیره سوئینگ‌ها در فایل"""
        try:
            # تبدیل datetime به string
            data_to_save = {}
            for session, swings in self.session_swings.items():
                data_to_save[session] = {
                    'highs': [
                        {**s, 'timestamp': s['timestamp'].isoformat() if isinstance(s['timestamp'], datetime) else s['timestamp']}
                        for s in swings['highs']
                    ],
                    'lows': [
                        {**s, 'timestamp': s['timestamp'].isoformat() if isinstance(s['timestamp'], datetime) else s['timestamp']}
                        for s in swings['lows']
                    ]
                }

            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطا در ذخیره سوئینگ‌ها: {e}")

    def load_swings(self):
        """بارگذاری سوئینگ‌ها از فایل"""
        try:
            if os.path.exists(self.persistence_file):
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # تبدیل string به datetime
                for session in data:
                    if session in self.session_swings:
                        self.session_swings[session] = {
                            'highs': [
                                {**s, 'timestamp': pd.to_datetime(s['timestamp'])}
                                for s in data[session].get('highs', [])
                            ],
                            'lows': [
                                {**s, 'timestamp': pd.to_datetime(s['timestamp'])}
                                for s in data[session].get('lows', [])
                            ]
                        }
        except Exception as e:
            print(f"خطا در بارگذاری سوئینگ‌ها: {e}")

    def find_swing_highs(self, df: pd.DataFrame,
                        left_bars: int = config.SWING_CONFIRMATION_CANDLES,
                        right_bars: int = config.SWING_CONFIRMATION_CANDLES) -> List[Dict]:
        """شناسایی سوئینگ های سقف"""
        swing_highs = []
        highs = df['high'].values

        for i in range(left_bars, len(df) - right_bars):
            is_swing_high = True

            # بررسی چپ
            for j in range(1, left_bars + 1):
                if highs[i] <= highs[i - j]:
                    is_swing_high = False
                    break

            if not is_swing_high:
                continue

            # بررسی راست
            for j in range(1, right_bars + 1):
                if highs[i] <= highs[i + j]:
                    is_swing_high = False
                    break

            if is_swing_high:
                # محاسبه قدرت
                left_diff = min([(highs[i] - highs[i - j]) / highs[i] * 100
                                for j in range(1, left_bars + 1)])
                right_diff = min([(highs[i] - highs[i + j]) / highs[i] * 100
                                 for j in range(1, right_bars + 1)])
                strength = min(left_diff, right_diff)

                if strength >= config.MIN_SWING_STRENGTH:
                    swing_highs.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'price': float(highs[i]),
                        'type': 'high',
                        'strength': float(strength)
                    })

        return swing_highs

    def find_swing_lows(self, df: pd.DataFrame,
                       left_bars: int = config.SWING_CONFIRMATION_CANDLES,
                       right_bars: int = config.SWING_CONFIRMATION_CANDLES) -> List[Dict]:
        """شناسایی سوئینگ های کف"""
        swing_lows = []
        lows = df['low'].values

        for i in range(left_bars, len(df) - right_bars):
            is_swing_low = True

            # بررسی چپ
            for j in range(1, left_bars + 1):
                if lows[i] >= lows[i - j]:
                    is_swing_low = False
                    break

            if not is_swing_low:
                continue

            # بررسی راست
            for j in range(1, right_bars + 1):
                if lows[i] >= lows[i + j]:
                    is_swing_low = False
                    break

            if is_swing_low:
                # محاسبه قدرت
                left_diff = min([(lows[i - j] - lows[i]) / lows[i] * 100
                                for j in range(1, left_bars + 1)])
                right_diff = min([(lows[i + j] - lows[i]) / lows[i] * 100
                                 for j in range(1, right_bars + 1)])
                strength = min(left_diff, right_diff)

                if strength >= config.MIN_SWING_STRENGTH:
                    swing_lows.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'price': float(lows[i]),
                        'type': 'low',
                        'strength': float(strength)
                    })

        return swing_lows

    def update_session_swings(self, session_name: str, df: pd.DataFrame):
        """
        بروزرسانی سوئینگ‌های یک سشن

        Args:
            session_name: نام سشن (tokyo, london, newyork)
            df: DataFrame حاوی داده‌های سشن
        """
        if session_name not in self.session_swings:
            return

        # شناسایی سوئینگ‌های جدید
        new_highs = self.find_swing_highs(df)
        new_lows = self.find_swing_lows(df)

        # افزودن به جدول (بدون تکرار)
        for swing in new_highs:
            # بررسی تکراری نبودن
            exists = any(
                abs(s['price'] - swing['price']) < 1 and
                abs((s['timestamp'] - swing['timestamp']).total_seconds()) < 3600
                for s in self.session_swings[session_name]['highs']
            )
            if not exists:
                self.session_swings[session_name]['highs'].append(swing)

        for swing in new_lows:
            exists = any(
                abs(s['price'] - swing['price']) < 1 and
                abs((s['timestamp'] - swing['timestamp']).total_seconds()) < 3600
                for s in self.session_swings[session_name]['lows']
            )
            if not exists:
                self.session_swings[session_name]['lows'].append(swing)

        # ذخیره تغییرات
        self.save_swings()

    def remove_touched_swing(self, session_name: str, swing_type: str, swing_price: float):
        """
        حذف سوئینگ تاچ شده

        Args:
            session_name: نام سشن
            swing_type: نوع ('high' یا 'low')
            swing_price: قیمت سوئینگ
        """
        if session_name not in self.session_swings:
            return

        swing_list = self.session_swings[session_name]['highs' if swing_type == 'high' else 'lows']

        # حذف سوئینگ
        self.session_swings[session_name]['highs' if swing_type == 'high' else 'lows'] = [
            s for s in swing_list if abs(s['price'] - swing_price) > 1
        ]

        # ذخیره
        self.save_swings()

    def get_previous_session_swings(self, current_session: str) -> Dict:
        """
        دریافت سوئینگ‌های سشن قبلی

        Args:
            current_session: سشن فعلی

        Returns:
            سوئینگ‌های سشن قبلی
        """
        # ترتیب سشن‌ها: tokyo -> london -> newyork -> tokyo
        session_order = ['tokyo', 'london', 'newyork']

        if current_session not in session_order:
            return {'highs': [], 'lows': []}

        current_index = session_order.index(current_session)
        previous_index = (current_index - 1) % 3
        previous_session = session_order[previous_index]

        return self.session_swings[previous_session]

    def check_swing_touch(self, current_price: float, swing_price: float) -> bool:
        """
        بررسی تاچ شدن سوئینگ

        Args:
            current_price: قیمت فعلی
            swing_price: قیمت سوئینگ

        Returns:
            True اگر تاچ شده
        """
        tolerance = swing_price * (config.SWING_TOUCH_TOLERANCE / 100)
        return abs(current_price - swing_price) <= tolerance

    def find_nearest_target(self, current_price: float, swings: List[Dict],
                           direction: str) -> Optional[Dict]:
        """
        پیدا کردن نزدیک‌ترین تارگت از سوئینگ‌ها

        Args:
            current_price: قیمت فعلی
            swings: لیست سوئینگ‌ها
            direction: جهت معامله ('buy' یا 'sell')

        Returns:
            نزدیک‌ترین سوئینگ هدف
        """
        if not swings:
            return None

        valid_swings = []

        for swing in swings:
            if direction == 'buy':
                # برای خرید، به دنبال highs بالاتر از قیمت فعلی
                if swing['price'] > current_price:
                    distance = swing['price'] - current_price
                    valid_swings.append({**swing, 'distance': distance})
            else:  # sell
                # برای فروش، به دنبال lows پایین‌تر از قیمت فعلی
                if swing['price'] < current_price:
                    distance = current_price - swing['price']
                    valid_swings.append({**swing, 'distance': distance})

        if not valid_swings:
            return None

        # مرتب‌سازی بر اساس فاصله
        valid_swings.sort(key=lambda x: x['distance'])

        return valid_swings[0]

    def print_session_swings(self):
        """چاپ جدول سوئینگ‌های تمام سشن‌ها"""
        print("\n" + "=" * 80)
        print("جدول سوئینگ‌های سشن‌ها".center(80))
        print("=" * 80)

        for session in ['tokyo', 'london', 'newyork']:
            swings = self.session_swings[session]
            print(f"\n📊 {session.upper()}:")
            print(f"   Swing Highs: {len(swings['highs'])} عدد")
            if swings['highs']:
                for i, swing in enumerate(swings['highs'][-3:], 1):  # آخرین 3 تا
                    print(f"      {i}. ${swing['price']:,.2f} (قدرت: {swing['strength']:.2f}%)")

            print(f"   Swing Lows: {len(swings['lows'])} عدد")
            if swings['lows']:
                for i, swing in enumerate(swings['lows'][-3:], 1):
                    print(f"      {i}. ${swing['price']:,.2f} (قدرت: {swing['strength']:.2f}%)")

        print("=" * 80 + "\n")


# تست
if __name__ == "__main__":
    print("تست مدیریت سوئینگ‌های سشن")
    print("-" * 70)

    manager = SessionSwingManager()

    # شبیه‌سازی داده
    dates = pd.date_range(start='2024-11-09 01:00', periods=50, freq='30min')
    prices = [50000 + i * 10 + np.random.randn() * 100 for i in range(50)]

    df = pd.DataFrame({
        'high': [p + abs(np.random.randn() * 50) for p in prices],
        'low': [p - abs(np.random.randn() * 50) for p in prices],
        'close': prices
    }, index=dates)

    # بروزرسانی سوئینگ‌های توکیو
    manager.update_session_swings('tokyo', df)

    # نمایش جدول
    manager.print_session_swings()

    # تست پیدا کردن تارگت
    previous_swings = manager.get_previous_session_swings('london')
    print(f"سوئینگ‌های سشن قبلی لندن (توکیو):")
    print(f"  Highs: {len(previous_swings['highs'])}")
    print(f"  Lows: {len(previous_swings['lows'])}")

    # پیدا کردن نزدیک‌ترین تارگت
    if previous_swings['highs']:
        target = manager.find_nearest_target(50500, previous_swings['highs'], 'buy')
        if target:
            print(f"\nنزدیک‌ترین تارگت برای خرید: ${target['price']:,.2f}")
