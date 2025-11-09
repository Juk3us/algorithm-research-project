"""
بک‌تست استراتژی سوئینگ‌های سشن
Backtest Session Swing Retouch Strategy
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
from typing import Dict, List, Tuple, Optional
import json

import config
from session_manager import SessionManager
from swing_detector import SessionSwingManager


class SessionBacktest:
    """بک‌تست استراتژی بر اساس سوئینگ‌های سشن"""

    def __init__(self, initial_balance: float = 1000.0):
        """
        مقداردهی اولیه

        Args:
            initial_balance: موجودی اولیه برای تست
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.session_manager = SessionManager()
        self.swing_manager = SessionSwingManager(persistence_file='backtest_swings.json')

        # معاملات
        self.trades = []
        self.open_position = None

        # آمار
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0

        # راه‌اندازی صرافی
        # سعی برای استفاده از صرافی‌های مختلف
        self.exchange = None
        for exchange_class in [ccxt.binance, ccxt.bybit, ccxt.okx]:
            try:
                self.exchange = exchange_class({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}
                })
                # تست اتصال
                self.exchange.load_markets()
                print(f"✅ اتصال به {self.exchange.name} برقرار شد")
                break
            except:
                continue

        if not self.exchange:
            print("⚠️  نمی‌توانم به هیچ صرافی متصل شوم - استفاده از داده‌های شبیه‌سازی شده")
            self.exchange = None

    def fetch_historical_data(self, days: int = 10) -> pd.DataFrame:
        """
        دریافت داده‌های تاریخی

        Args:
            days: تعداد روزهای گذشته

        Returns:
            DataFrame حاوی داده‌های OHLCV
        """
        print(f"\n📥 دریافت داده‌های {days} روز گذشته...")

        # اگر صرافی متصل است، از API استفاده کن
        if self.exchange:
            try:
                # محاسبه timestamp
                since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

                # دریافت داده‌ها
                ohlcv = self.exchange.fetch_ohlcv(
                    config.MARKET_SYMBOL,
                    config.CHART_TIMEFRAME,
                    since=since,
                    limit=1000
                )

                # تبدیل به DataFrame
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )

                # تبدیل timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

                print(f"✅ دریافت {len(df)} کندل واقعی از {df.index[0]} تا {df.index[-1]}")
                return df

            except Exception as e:
                print(f"⚠️  خطا در دریافت داده‌های واقعی: {e}")
                print("🔄 استفاده از داده‌های شبیه‌سازی شده...")

        # تولید داده‌های شبیه‌سازی شده
        return self._generate_mock_data(days)

    def _generate_mock_data(self, days: int) -> pd.DataFrame:
        """
        تولید داده‌های شبیه‌سازی شده برای تست

        Args:
            days: تعداد روزها

        Returns:
            DataFrame حاوی داده‌های mock
        """
        # محاسبه تعداد کندل‌ها (30 دقیقه)
        candles_per_day = 24 * 2  # 48 کندل در روز
        total_candles = days * candles_per_day

        # زمان شروع
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # تولید زمان‌ها
        timestamps = pd.date_range(start=start_time, end=end_time, periods=total_candles)

        # قیمت پایه BTC
        base_price = 90000.0

        # تولید قیمت‌ها با روند تصادفی
        np.random.seed(42)  # برای قابل تکرار بودن
        prices = []
        current_price = base_price

        for i in range(total_candles):
            # حرکت تصادفی با bias کمی صعودی
            change_pct = np.random.normal(0.001, 0.01)  # 0.1% mean, 1% std
            current_price = current_price * (1 + change_pct)

            # جلوگیری از قیمت‌های غیرواقعی
            current_price = max(60000, min(120000, current_price))

            prices.append(current_price)

        # ساخت DataFrame
        data = []
        for i, timestamp in enumerate(timestamps):
            price = prices[i]
            # شبیه‌سازی high/low
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            open_price = low + (high - low) * np.random.random()
            close_price = low + (high - low) * np.random.random()

            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': np.random.uniform(100, 1000)
            })

        df = pd.DataFrame(data, index=timestamps)
        print(f"✅ تولید {len(df)} کندل شبیه‌سازی شده از {df.index[0]} تا {df.index[-1]}")
        print(f"   قیمت شروع: ${df['close'].iloc[0]:,.2f} | قیمت پایان: ${df['close'].iloc[-1]:,.2f}")

        return df

    def identify_session(self, timestamp: pd.Timestamp) -> Optional[str]:
        """
        شناسایی سشن برای یک timestamp

        Args:
            timestamp: زمان

        Returns:
            نام سشن یا None
        """
        # تبدیل به timezone تهران
        tz = pytz.timezone(config.TIMEZONE)
        dt = timestamp.tz_localize('UTC').tz_convert(tz)

        for session_key in ['tokyo', 'london', 'newyork']:
            if self.session_manager.is_session_active(session_key, dt):
                return session_key

        return None

    def is_in_overlap(self, timestamp: pd.Timestamp) -> Tuple[bool, Optional[Dict]]:
        """
        بررسی قرار گرفتن در overlap

        Args:
            timestamp: زمان

        Returns:
            (در overlap است, اطلاعات overlap)
        """
        tz = pytz.timezone(config.TIMEZONE)
        dt = timestamp.tz_localize('UTC').tz_convert(tz)

        should_trade, overlap_info = self.session_manager.should_trade(dt)
        return should_trade, overlap_info

    def detect_trend(self, df: pd.DataFrame, current_idx: int) -> Tuple[str, float]:
        """
        تشخیص روند

        Args:
            df: DataFrame کامل
            current_idx: ایندکس فعلی

        Returns:
            (روند, قدرت)
        """
        # بررسی 10 کندل قبلی
        start_idx = max(0, current_idx - config.TREND_ANALYSIS_PERIOD)
        recent = df.iloc[start_idx:current_idx+1]

        if len(recent) < 2:
            return 'neutral', 0

        # محاسبه تغییر قیمت
        price_change = recent['close'].iloc[-1] - recent['close'].iloc[0]
        price_change_pct = (price_change / recent['close'].iloc[0]) * 100

        # محاسبه momentum
        momentum = recent['close'].diff().mean()

        # تشخیص روند
        if price_change > 0 and momentum > 0:
            return 'bullish', abs(price_change_pct)
        elif price_change < 0 and momentum < 0:
            return 'bearish', abs(price_change_pct)
        else:
            return 'neutral', 0

    def calculate_stop_loss(self, entry_price: float, direction: str, df: pd.DataFrame) -> float:
        """
        محاسبه استاپ لاس با ATR

        Args:
            entry_price: قیمت ورود
            direction: جهت معامله
            df: DataFrame

        Returns:
            قیمت استاپ لاس
        """
        # محاسبه ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(config.ATR_PERIOD).mean().iloc[-1]

        if direction == 'buy':
            stop_loss = entry_price - (atr * config.ATR_MULTIPLIER)
        else:  # sell
            stop_loss = entry_price + (atr * config.ATR_MULTIPLIER)

        return stop_loss

    def open_trade(self, signal: str, entry_price: float, target_price: float,
                   stop_loss: float, session: str, trend: str, timestamp: pd.Timestamp):
        """
        باز کردن معامله

        Args:
            signal: 'buy' یا 'sell'
            entry_price: قیمت ورود
            target_price: قیمت هدف
            stop_loss: قیمت استاپ لاس
            session: سشن فعلی
            trend: روند
            timestamp: زمان ورود
        """
        # محاسبه ریسک
        if signal == 'buy':
            risk = entry_price - stop_loss
            reward = target_price - entry_price
        else:  # sell
            risk = stop_loss - entry_price
            reward = entry_price - target_price

        # محاسبه حجم معامله
        risk_amount = self.balance * config.MAX_TRADE_RISK
        position_size = risk_amount / risk if risk > 0 else 0

        if position_size <= 0:
            return

        self.open_position = {
            'signal': signal,
            'entry_price': entry_price,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'position_size': position_size,
            'entry_time': timestamp,
            'session': session,
            'trend': trend,
            'risk': risk,
            'reward': reward,
            'risk_reward_ratio': reward / risk if risk > 0 else 0
        }

        print(f"\n{'🟢 خرید' if signal == 'buy' else '🔴 فروش'} | "
              f"قیمت: ${entry_price:,.2f} | "
              f"تارگت: ${target_price:,.2f} | "
              f"SL: ${stop_loss:,.2f} | "
              f"R/R: {self.open_position['risk_reward_ratio']:.2f}")

    def check_position(self, current_candle: pd.Series):
        """
        بررسی پوزیشن باز

        Args:
            current_candle: کندل فعلی
        """
        if not self.open_position:
            return

        pos = self.open_position
        current_price = current_candle['close']

        # بررسی رسیدن به تارگت
        target_hit = False
        stop_hit = False

        if pos['signal'] == 'buy':
            if current_candle['high'] >= pos['target_price']:
                target_hit = True
                exit_price = pos['target_price']
            elif current_candle['low'] <= pos['stop_loss']:
                stop_hit = True
                exit_price = pos['stop_loss']
        else:  # sell
            if current_candle['low'] <= pos['target_price']:
                target_hit = True
                exit_price = pos['target_price']
            elif current_candle['high'] >= pos['stop_loss']:
                stop_hit = True
                exit_price = pos['stop_loss']

        if target_hit or stop_hit:
            self.close_trade(exit_price, current_candle.name, target_hit)

    def close_trade(self, exit_price: float, exit_time: pd.Timestamp, won: bool):
        """
        بستن معامله

        Args:
            exit_price: قیمت خروج
            exit_time: زمان خروج
            won: آیا سودآور بود
        """
        if not self.open_position:
            return

        pos = self.open_position

        # محاسبه سود/ضرر
        if pos['signal'] == 'buy':
            pnl = (exit_price - pos['entry_price']) * pos['position_size']
        else:  # sell
            pnl = (pos['entry_price'] - exit_price) * pos['position_size']

        pnl_pct = (pnl / self.balance) * 100

        # بروزرسانی موجودی
        self.balance += pnl

        # ثبت معامله
        trade_record = {
            **pos,
            'exit_price': exit_price,
            'exit_time': exit_time,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'won': won,
            'balance_after': self.balance
        }

        self.trades.append(trade_record)

        # بروزرسانی آمار
        self.total_trades += 1
        if won:
            self.winning_trades += 1
            self.total_profit += pnl
            print(f"✅ سود: ${pnl:,.2f} ({pnl_pct:.2f}%) | موجودی: ${self.balance:,.2f}")
        else:
            self.losing_trades += 1
            self.total_loss += abs(pnl)
            print(f"❌ ضرر: ${pnl:,.2f} ({pnl_pct:.2f}%) | موجودی: ${self.balance:,.2f}")

        # حذف سوئینگ تاچ شده
        if won:
            swing_type = 'high' if pos['signal'] == 'buy' else 'low'
            # پیدا کردن سشن قبلی
            session_order = ['tokyo', 'london', 'newyork']
            current_idx = session_order.index(pos['session'])
            previous_idx = (current_idx - 1) % 3
            previous_session = session_order[previous_idx]

            self.swing_manager.remove_touched_swing(
                previous_session,
                swing_type,
                pos['target_price']
            )

        # پاک کردن پوزیشن
        self.open_position = None

    def run_backtest(self, df: pd.DataFrame):
        """
        اجرای بک‌تست

        Args:
            df: DataFrame حاوی داده‌های تاریخی
        """
        print("\n" + "=" * 80)
        print("شروع بک‌تست استراتژی سوئینگ‌های سشن".center(80))
        print("=" * 80)

        # متغیرهای سشن
        current_session = None
        session_data = {}
        session_count = 0

        # حلقه روی تمام کندل‌ها
        for idx in range(config.MIN_CANDLES, len(df)):
            candle = df.iloc[idx]
            timestamp = candle.name

            # شناسایی سشن
            session = self.identify_session(timestamp)

            # اگر سشن تغییر کرد
            if session and session != current_session:
                # بروزرسانی سوئینگ‌های سشن قبلی
                if current_session and len(session_data) > 0:
                    session_df = pd.DataFrame.from_dict(session_data, orient='index')
                    self.swing_manager.update_session_swings(current_session, session_df)
                    session_count += 1

                    print(f"\n📊 سشن {session_count}: {current_session.upper()} "
                          f"({len(session_data)} کندل) - سوئینگ‌ها بروزرسانی شد")

                # شروع سشن جدید
                current_session = session
                session_data = {}

            # افزودن کندل به داده‌های سشن
            if current_session:
                session_data[timestamp] = {
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close'],
                    'volume': candle['volume']
                }

            # بررسی پوزیشن باز
            if self.open_position:
                self.check_position(candle)

            # اگر پوزیشن باز نداریم، به دنبال سیگنال باش
            if not self.open_position:
                # بررسی overlap
                in_overlap, overlap_info = self.is_in_overlap(timestamp)

                if in_overlap and current_session:
                    # تشخیص روند
                    trend, trend_strength = self.detect_trend(df, idx)

                    if trend != 'neutral' and trend_strength >= config.MIN_PRICE_CHANGE:
                        # دریافت سوئینگ‌های سشن قبلی
                        previous_swings = self.swing_manager.get_previous_session_swings(current_session)
                        current_price = candle['close']

                        signal = None
                        target_swing = None

                        if trend == 'bullish':
                            # روند صعودی → فروش
                            signal = 'sell'
                            target_swing = self.swing_manager.find_nearest_target(
                                current_price, previous_swings['lows'], 'sell'
                            )
                        elif trend == 'bearish':
                            # روند نزولی → خرید
                            signal = 'buy'
                            target_swing = self.swing_manager.find_nearest_target(
                                current_price, previous_swings['highs'], 'buy'
                            )

                        if target_swing:
                            # محاسبه استاپ لاس
                            stop_loss = self.calculate_stop_loss(
                                current_price,
                                signal,
                                df.iloc[:idx+1]
                            )

                            # باز کردن معامله
                            self.open_trade(
                                signal,
                                current_price,
                                target_swing['price'],
                                stop_loss,
                                current_session,
                                trend,
                                timestamp
                            )

        # بستن سشن آخر
        if current_session and len(session_data) > 0:
            session_df = pd.DataFrame.from_dict(session_data, orient='index')
            self.swing_manager.update_session_swings(current_session, session_df)
            session_count += 1

        print(f"\n📊 مجموع سشن‌های پردازش شده: {session_count}")

    def print_results(self):
        """چاپ نتایج بک‌تست"""
        print("\n" + "=" * 80)
        print("نتایج بک‌تست".center(80))
        print("=" * 80)

        print(f"\n💰 عملکرد مالی:")
        print(f"   موجودی اولیه: ${self.initial_balance:,.2f}")
        print(f"   موجودی نهایی: ${self.balance:,.2f}")
        profit = self.balance - self.initial_balance
        profit_pct = (profit / self.initial_balance) * 100
        print(f"   {'سود' if profit > 0 else 'ضرر'} خالص: ${profit:,.2f} ({profit_pct:+.2f}%)")

        print(f"\n📊 آمار معاملات:")
        print(f"   مجموع معاملات: {self.total_trades}")
        print(f"   معاملات سودآور: {self.winning_trades}")
        print(f"   معاملات ضررده: {self.losing_trades}")

        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            print(f"   نرخ برد: {win_rate:.2f}%")

            if self.winning_trades > 0:
                avg_profit = self.total_profit / self.winning_trades
                print(f"   میانگین سود: ${avg_profit:,.2f}")

            if self.losing_trades > 0:
                avg_loss = self.total_loss / self.losing_trades
                print(f"   میانگین ضرر: ${avg_loss:,.2f}")

            if self.losing_trades > 0 and self.winning_trades > 0:
                profit_factor = self.total_profit / self.total_loss
                print(f"   Profit Factor: {profit_factor:.2f}")

        # نمایش جدول سوئینگ‌ها
        print("\n📈 جدول سوئینگ‌های نهایی:")
        self.swing_manager.print_session_swings()

        # نمایش معاملات
        if self.trades:
            print("\n📋 لیست معاملات:")
            print("-" * 80)
            for i, trade in enumerate(self.trades, 1):
                status = "✅ سود" if trade['won'] else "❌ ضرر"
                print(f"{i}. {status} | "
                      f"{trade['signal'].upper()} | "
                      f"سشن: {trade['session'].upper()} | "
                      f"ورود: ${trade['entry_price']:,.2f} → "
                      f"خروج: ${trade['exit_price']:,.2f} | "
                      f"P/L: ${trade['pnl']:,.2f} ({trade['pnl_pct']:+.2f}%)")

        print("\n" + "=" * 80)

        # ذخیره نتایج در فایل
        self.save_results()

    def save_results(self):
        """ذخیره نتایج در فایل JSON"""
        results = {
            'summary': {
                'initial_balance': self.initial_balance,
                'final_balance': self.balance,
                'profit': self.balance - self.initial_balance,
                'profit_pct': ((self.balance - self.initial_balance) / self.initial_balance) * 100,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
                'total_profit': self.total_profit,
                'total_loss': self.total_loss,
                'profit_factor': (self.total_profit / self.total_loss) if self.total_loss > 0 else 0
            },
            'trades': [
                {
                    **trade,
                    'entry_time': trade['entry_time'].isoformat(),
                    'exit_time': trade['exit_time'].isoformat()
                }
                for trade in self.trades
            ]
        }

        with open('backtest_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 نتایج در فایل backtest_results.json ذخیره شد")


def main():
    """تابع اصلی"""
    print("🔬 بک‌تست استراتژی سوئینگ‌های سشن")
    print("=" * 80)

    # ایجاد نمونه
    backtest = SessionBacktest(initial_balance=1000.0)

    # دریافت داده‌های تاریخی (10 روز)
    df = backtest.fetch_historical_data(days=10)

    if df is None or len(df) == 0:
        print("❌ خطا در دریافت داده‌ها")
        return

    # اجرای بک‌تست
    backtest.run_backtest(df)

    # نمایش نتایج
    backtest.print_results()


if __name__ == "__main__":
    main()
