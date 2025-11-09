"""
شناسایی سوئینگ‌ها و تحلیل تاچ سوئینگ‌های قبلی
Swing Detection and Previous Swing Touch Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import config


class SwingDetector:
    """شناسایی و تحلیل سوئینگ‌های قیمتی"""

    def __init__(self):
        """مقداردهی اولیه"""
        self.swing_highs = []  # لیست سوئینگ های سقف
        self.swing_lows = []   # لیست سوئینگ های کف
        self.last_analysis_time = None

    def find_swing_highs(self, df: pd.DataFrame,
                        left_bars: int = config.SWING_CONFIRMATION_CANDLES,
                        right_bars: int = config.SWING_CONFIRMATION_CANDLES) -> List[Dict]:
        """
        شناسایی سوئینگ های سقف (Swing Highs)

        Args:
            df: DataFrame حاوی داده‌های قیمت
            left_bars: تعداد کندل‌های سمت چپ برای تأیید
            right_bars: تعداد کندل‌های سمت راست برای تأیید

        Returns:
            لیست سوئینگ های سقف
        """
        swing_highs = []
        highs = df['high'].values

        # از اول تا قبل از right_bars آخر
        for i in range(left_bars, len(df) - right_bars):
            is_swing_high = True

            # بررسی کندل‌های سمت چپ
            for j in range(1, left_bars + 1):
                if highs[i] <= highs[i - j]:
                    is_swing_high = False
                    break

            if not is_swing_high:
                continue

            # بررسی کندل‌های سمت راست
            for j in range(1, right_bars + 1):
                if highs[i] <= highs[i + j]:
                    is_swing_high = False
                    break

            if is_swing_high:
                # محاسبه قدرت سوئینگ
                left_diff = min([(highs[i] - highs[i - j]) / highs[i] * 100
                                for j in range(1, left_bars + 1)])
                right_diff = min([(highs[i] - highs[i + j]) / highs[i] * 100
                                 for j in range(1, right_bars + 1)])
                strength = min(left_diff, right_diff)

                # فقط سوئینگ‌های قوی
                if strength >= config.MIN_SWING_STRENGTH:
                    swing_highs.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'price': highs[i],
                        'type': 'high',
                        'strength': strength,
                        'touched': False
                    })

        return swing_highs

    def find_swing_lows(self, df: pd.DataFrame,
                       left_bars: int = config.SWING_CONFIRMATION_CANDLES,
                       right_bars: int = config.SWING_CONFIRMATION_CANDLES) -> List[Dict]:
        """
        شناسایی سوئینگ های کف (Swing Lows)

        Args:
            df: DataFrame حاوی داده‌های قیمت
            left_bars: تعداد کندل‌های سمت چپ برای تأیید
            right_bars: تعداد کندل‌های سمت راست برای تأیید

        Returns:
            لیست سوئینگ های کف
        """
        swing_lows = []
        lows = df['low'].values

        # از اول تا قبل از right_bars آخر
        for i in range(left_bars, len(df) - right_bars):
            is_swing_low = True

            # بررسی کندل‌های سمت چپ
            for j in range(1, left_bars + 1):
                if lows[i] >= lows[i - j]:
                    is_swing_low = False
                    break

            if not is_swing_low:
                continue

            # بررسی کندل‌های سمت راست
            for j in range(1, right_bars + 1):
                if lows[i] >= lows[i + j]:
                    is_swing_low = False
                    break

            if is_swing_low:
                # محاسبه قدرت سوئینگ
                left_diff = min([(lows[i - j] - lows[i]) / lows[i] * 100
                                for j in range(1, left_bars + 1)])
                right_diff = min([(lows[i + j] - lows[i]) / lows[i] * 100
                                 for j in range(1, right_bars + 1)])
                strength = min(left_diff, right_diff)

                # فقط سوئینگ‌های قوی
                if strength >= config.MIN_SWING_STRENGTH:
                    swing_lows.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'price': lows[i],
                        'type': 'low',
                        'strength': strength,
                        'touched': False
                    })

        return swing_lows

    def identify_higher_highs_lower_lows(self, swing_highs: List[Dict],
                                         swing_lows: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        شناسایی Higher Highs و Lower Lows

        Args:
            swing_highs: لیست سوئینگ های سقف
            swing_lows: لیست سوئینگ های کف

        Returns:
            (higher_highs, lower_lows)
        """
        higher_highs = []
        lower_lows = []

        # شناسایی Higher Highs
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] > swing_highs[i-1]['price']:
                swing_highs[i]['pattern'] = 'higher_high'
                higher_highs.append(swing_highs[i])
            elif swing_highs[i]['price'] < swing_highs[i-1]['price']:
                swing_highs[i]['pattern'] = 'lower_high'

        # شناسایی Lower Lows
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] < swing_lows[i-1]['price']:
                swing_lows[i]['pattern'] = 'lower_low'
                lower_lows.append(swing_lows[i])
            elif swing_lows[i]['price'] > swing_lows[i-1]['price']:
                swing_lows[i]['pattern'] = 'higher_low'

        return higher_highs, lower_lows

    def check_swing_touch(self, current_price: float, swing_level: float,
                         swing_type: str) -> bool:
        """
        بررسی تاچ شدن سوئینگ

        Args:
            current_price: قیمت فعلی
            swing_level: سطح سوئینگ
            swing_type: نوع سوئینگ ('high' یا 'low')

        Returns:
            True اگر سوئینگ تاچ شده
        """
        tolerance = swing_level * (config.SWING_TOUCH_TOLERANCE / 100)

        if swing_type == 'high':
            # برای سوئینگ سقف، قیمت باید به سطح نزدیک شده یا بالاتر رفته باشد
            return abs(current_price - swing_level) <= tolerance or current_price > swing_level
        else:  # 'low'
            # برای سوئینگ کف، قیمت باید به سطح نزدیک شده یا پایین‌تر آمده باشد
            return abs(current_price - swing_level) <= tolerance or current_price < swing_level

    def analyze_market(self, df: pd.DataFrame) -> Dict:
        """
        تحلیل کامل بازار و شناسایی سوئینگ‌ها

        Args:
            df: DataFrame حاوی داده‌های قیمت

        Returns:
            دیکشنری حاوی تحلیل کامل
        """
        if len(df) < config.MIN_CANDLES:
            return {
                'valid': False,
                'reason': 'تعداد کندل کافی نیست'
            }

        # محدود کردن به lookback period
        lookback_df = df.tail(config.SWING_LOOKBACK)

        # شناسایی سوئینگ‌ها
        swing_highs = self.find_swing_highs(lookback_df)
        swing_lows = self.find_swing_lows(lookback_df)

        # شناسایی الگوها
        higher_highs, lower_lows = self.identify_higher_highs_lower_lows(
            swing_highs, swing_lows
        )

        # ذخیره برای استفاده بعدی
        self.swing_highs = swing_highs
        self.swing_lows = swing_lows
        self.last_analysis_time = datetime.now()

        return {
            'valid': True,
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'higher_highs': higher_highs,
            'lower_lows': lower_lows,
            'total_swing_highs': len(swing_highs),
            'total_swing_lows': len(swing_lows),
            'total_higher_highs': len(higher_highs),
            'total_lower_lows': len(lower_lows)
        }

    def find_untouched_swings(self, df: pd.DataFrame,
                             analysis: Dict) -> Tuple[List[Dict], List[Dict]]:
        """
        پیدا کردن سوئینگ‌هایی که هنوز تاچ نشدند

        Args:
            df: DataFrame حاوی داده‌های قیمت
            analysis: نتیجه تحلیل از analyze_market

        Returns:
            (untouched_highs, untouched_lows)
        """
        if not analysis['valid']:
            return [], []

        current_price = df['close'].iloc[-1]
        untouched_highs = []
        untouched_lows = []

        # بررسی سوئینگ های سقف
        for swing in analysis['swing_highs']:
            if not swing.get('touched', False):
                # بررسی تاچ شدن
                if self.check_swing_touch(current_price, swing['price'], 'high'):
                    swing['touched'] = True
                    swing['touch_time'] = datetime.now()
                else:
                    untouched_highs.append(swing)

        # بررسی سوئینگ های کف
        for swing in analysis['swing_lows']:
            if not swing.get('touched', False):
                # بررسی تاچ شدن
                if self.check_swing_touch(current_price, swing['price'], 'low'):
                    swing['touched'] = True
                    swing['touch_time'] = datetime.now()
                else:
                    untouched_lows.append(swing)

        return untouched_highs, untouched_lows

    def get_nearest_untouched_swing(self, current_price: float,
                                   untouched_highs: List[Dict],
                                   untouched_lows: List[Dict]) -> Optional[Dict]:
        """
        پیدا کردن نزدیک‌ترین سوئینگ تاچ نشده

        Args:
            current_price: قیمت فعلی
            untouched_highs: سوئینگ های سقف تاچ نشده
            untouched_lows: سوئینگ های کف تاچ نشده

        Returns:
            نزدیک‌ترین سوئینگ یا None
        """
        all_swings = []

        for swing in untouched_highs:
            distance = abs(current_price - swing['price'])
            all_swings.append({
                **swing,
                'distance': distance,
                'distance_pct': (distance / current_price) * 100
            })

        for swing in untouched_lows:
            distance = abs(current_price - swing['price'])
            all_swings.append({
                **swing,
                'distance': distance,
                'distance_pct': (distance / current_price) * 100
            })

        if not all_swings:
            return None

        # مرتب‌سازی بر اساس فاصله
        all_swings.sort(key=lambda x: x['distance'])

        return all_swings[0]

    def generate_trading_signal(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[Dict]]:
        """
        تولید سیگنال معاملاتی بر اساس تاچ سوئینگ‌ها

        اصل اول: تمام سوئینگ‌ها یک بار دیگر تاچ می‌شوند

        Args:
            df: DataFrame حاوی داده‌های قیمت

        Returns:
            (signal: 'buy'/'sell'/None, swing_info)
        """
        # تحلیل بازار
        analysis = self.analyze_market(df)
        if not analysis['valid']:
            return None, None

        # پیدا کردن سوئینگ‌های تاچ نشده
        untouched_highs, untouched_lows = self.find_untouched_swings(df, analysis)

        # قیمت فعلی
        current_price = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]

        # بررسی تاچ Higher Highs → سیگنال فروش
        if config.TRADE_ON_HIGHER_HIGHS:
            for swing in analysis['higher_highs']:
                if self.check_swing_touch(current_high, swing['price'], 'high'):
                    return 'sell', {
                        'reason': 'تاچ Higher High',
                        'swing_level': swing['price'],
                        'swing_type': 'higher_high',
                        'current_price': current_price,
                        'strength': swing.get('strength', 0)
                    }

        # بررسی تاچ Lower Lows → سیگنال خرید
        if config.TRADE_ON_LOWER_LOWS:
            for swing in analysis['lower_lows']:
                if self.check_swing_touch(current_low, swing['price'], 'low'):
                    return 'buy', {
                        'reason': 'تاچ Lower Low',
                        'swing_level': swing['price'],
                        'swing_type': 'lower_low',
                        'current_price': current_price,
                        'strength': swing.get('strength', 0)
                    }

        return None, None

    def print_analysis(self, analysis: Dict):
        """چاپ نتایج تحلیل"""
        if not analysis['valid']:
            print(f"❌ تحلیل نامعتبر: {analysis.get('reason', 'نامشخص')}")
            return

        print("\n" + "=" * 70)
        print("تحلیل سوئینگ‌های بازار".center(70))
        print("=" * 70)

        print(f"\n📊 آمار کلی:")
        print(f"   تعداد Swing Highs: {analysis['total_swing_highs']}")
        print(f"   تعداد Swing Lows: {analysis['total_swing_lows']}")
        print(f"   تعداد Higher Highs: {analysis['total_higher_highs']}")
        print(f"   تعداد Lower Lows: {analysis['total_lower_lows']}")

        if analysis['higher_highs']:
            print(f"\n🔺 آخرین Higher High:")
            hh = analysis['higher_highs'][-1]
            print(f"   قیمت: ${hh['price']:,.2f}")
            print(f"   قدرت: {hh.get('strength', 0):.2f}%")

        if analysis['lower_lows']:
            print(f"\n🔻 آخرین Lower Low:")
            ll = analysis['lower_lows'][-1]
            print(f"   قیمت: ${ll['price']:,.2f}")
            print(f"   قدرت: {ll.get('strength', 0):.2f}%")

        print("=" * 70 + "\n")


# تست مستقل ماژول
if __name__ == "__main__":
    print("تست شناسایی سوئینگ‌ها")
    print("-" * 70)

    # ایجاد داده تستی
    dates = pd.date_range(start='2024-01-01', periods=100, freq='30min')
    np.random.seed(42)

    # شبیه‌سازی قیمت با سوئینگ‌های واضح
    price = 50000
    prices = []
    for i in range(100):
        price += np.random.randn() * 100
        if i % 10 == 0:
            price += 500  # ایجاد سوئینگ صعودی
        elif i % 15 == 0:
            price -= 300  # ایجاد سوئینگ نزولی
        prices.append(price)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + abs(np.random.randn() * 50) for p in prices],
        'low': [p - abs(np.random.randn() * 50) for p in prices],
        'close': prices,
        'volume': [1000 + np.random.randint(0, 500) for _ in range(100)]
    })
    df.set_index('timestamp', inplace=True)

    # ایجاد detector
    detector = SwingDetector()

    # تحلیل
    analysis = detector.analyze_market(df)
    detector.print_analysis(analysis)

    # تولید سیگنال
    signal, info = detector.generate_trading_signal(df)
    if signal:
        print(f"\n✅ سیگنال: {signal.upper()}")
        print(f"   دلیل: {info['reason']}")
        print(f"   سطح سوئینگ: ${info['swing_level']:,.2f}")
        print(f"   قیمت فعلی: ${info['current_price']:,.2f}")
    else:
        print("\n⚠️  سیگنال معاملاتی پیدا نشد")
