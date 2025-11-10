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

    def __init__(self, initial_balance: float = 1000.0, symbol: str = None):
        """
        مقداردهی اولیه

        Args:
            initial_balance: موجودی اولیه برای تست
            symbol: نماد معاملاتی (پیش‌فرض: از config)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.symbol = symbol or config.MARKET_SYMBOL
        self.session_manager = SessionManager()

        # فایل جداگانه برای هر نماد برای جلوگیری از قاطی شدن سوئینگ‌ها
        safe_symbol = self.symbol.replace('/', '_').replace('\\', '_')
        self.swing_manager = SessionSwingManager(
            persistence_file=f'backtest_swings_{safe_symbol}.json'
        )

        # معاملات
        self.trades = []
        self.open_position = None  # فقط یک پوزیشن در هر زمان

        # آمار
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0

        # متغیرهای استراتژی جدید: تشخیص روند در overlap
        self.was_in_overlap = False
        self.overlap_trend = None
        self.overlap_trend_strength = 0

        # راه‌اندازی صرافی
        # سعی برای استفاده از صرافی‌های مختلف
        self.exchange = None

        # اگر symbol شامل AUD/USD یا جفت‌ارزهای فارکس باشد
        # از داده‌های شبیه‌سازی استفاده کن
        if 'AUD' in symbol or 'EUR' in symbol or 'GBP' in symbol:
            print(f"⚠️  {symbol} یک جفت‌ارز فارکس است")
            print("⚠️  استفاده از داده‌های شبیه‌سازی شده")
            self.exchange = None
        else:
            # برای ارزهای دیجیتال از KuCoin استفاده کن
            try:
                print("🔌 اتصال به KuCoin...")
                self.exchange = ccxt.kucoin({
                    'apiKey': '642080b050d2730001387aa7',
                    'secret': 'Hanibal@293',
                    'enableRateLimit': True,
                    'timeout': 30000
                })
                # تست اتصال
                self.exchange.load_markets()
                print(f"✅ اتصال به {self.exchange.name} برقرار شد")
            except Exception as e:
                print(f"⚠️  خطا در اتصال به KuCoin: {e}")
                print("⚠️  استفاده از داده‌های شبیه‌سازی شده")
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
                    self.symbol,
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

        # تشخیص نوع نماد و قیمت پایه
        if 'BTC' in self.symbol or 'bitcoin' in self.symbol.lower():
            base_price = 90000.0
            min_price = 60000
            max_price = 120000
            volatility = 0.01  # 1%
        elif 'AUD' in self.symbol or 'aud' in self.symbol.lower():
            base_price = 0.65  # AUD/USD معمولاً بین 0.6-0.8
            min_price = 0.55
            max_price = 0.75
            volatility = 0.005  # 0.5% - فارکس کمتر نوسان دارد
        else:
            # پیش‌فرض برای ارزهای دیگر
            base_price = 1.0
            min_price = 0.5
            max_price = 2.0
            volatility = 0.01

        # تولید قیمت‌ها با روند تصادفی
        np.random.seed(42)  # برای قابل تکرار بودن
        prices = []
        current_price = base_price

        for i in range(total_candles):
            # حرکت تصادفی با bias کمی صعودی
            change_pct = np.random.normal(0.0001, volatility)
            current_price = current_price * (1 + change_pct)

            # جلوگیری از قیمت‌های غیرواقعی
            current_price = max(min_price, min(max_price, current_price))

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

        # فرمت قیمت بر اساس نوع نماد
        if 'AUD' in self.symbol or 'EUR' in self.symbol or 'GBP' in self.symbol:
            # فارکس - 5 رقم اعشار
            print(f"   قیمت شروع: {df['close'].iloc[0]:.5f} | قیمت پایان: {df['close'].iloc[-1]:.5f}")
        else:
            # کریپتو - 2 رقم اعشار
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

    def check_position(self, current_candle: pd.Series):
        """
        بررسی پوزیشن باز

        Args:
            current_candle: کندل فعلی
        """
        if not self.open_position:
            return

        current_price = current_candle['close']

        # بررسی رسیدن به تارگت
        target_hit = False
        stop_hit = False

        if self.open_position['signal'] == 'buy':
            if current_candle['high'] >= self.open_position['target_price']:
                target_hit = True
                exit_price = self.open_position['target_price']
            elif current_candle['low'] <= self.open_position['stop_loss']:
                stop_hit = True
                exit_price = self.open_position['stop_loss']
        else:  # sell
            if current_candle['low'] <= self.open_position['target_price']:
                target_hit = True
                exit_price = self.open_position['target_price']
            elif current_candle['high'] >= self.open_position['stop_loss']:
                stop_hit = True
                exit_price = self.open_position['stop_loss']

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

        position = self.open_position

        # محاسبه سود/ضرر
        if position['signal'] == 'buy':
            pnl = (exit_price - position['entry_price']) * position['position_size']
        else:  # sell
            pnl = (position['entry_price'] - exit_price) * position['position_size']

        pnl_pct = (pnl / self.balance) * 100

        # بروزرسانی موجودی
        self.balance += pnl

        # ثبت معامله
        trade_record = {
            **position,
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
        else:
            self.losing_trades += 1
            self.total_loss += abs(pnl)

        # چاپ نتیجه (بر اساس pnl واقعی، نه won)
        if pnl > 0:
            print(f"✅ سود: ${pnl:,.2f} ({pnl_pct:.2f}%) | موجودی: ${self.balance:,.2f}")
        else:
            print(f"❌ ضرر: ${pnl:,.2f} ({pnl_pct:.2f}%) | موجودی: ${self.balance:,.2f}")

        # حذف سوئینگ تاچ شده
        if won:
            swing_type = 'high' if position['signal'] == 'buy' else 'low'
            # پیدا کردن سشن قبلی
            session_order = ['tokyo', 'london', 'newyork']
            current_idx = session_order.index(position['session'])
            previous_idx = (current_idx - 1) % 3
            previous_session = session_order[previous_idx]

            self.swing_manager.remove_touched_swing(
                previous_session,
                swing_type,
                position['target_price']
            )

        # حذف پوزیشن
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

                # مرحله 1: اگر در overlap هستیم، فقط روند را شناسایی و ذخیره کن (معامله نکن!)
                if in_overlap and current_session:
                    # تشخیص روند در طول overlap
                    trend, trend_strength = self.detect_trend(df, idx)

                    # ذخیره روند برای استفاده بعد از overlap
                    self.overlap_trend = trend
                    self.overlap_trend_strength = trend_strength
                    self.was_in_overlap = True

                    # ادامه به کندل بعدی - هنوز معامله نکن!

                # مرحله 2: اگر از overlap خارج شدیم، الان معامله کن!
                elif not in_overlap and self.was_in_overlap and current_session:
                    # از overlap خارج شدیم و سشن جدید شروع شده
                    print(f"\n🔔 خروج از overlap - سشن {current_session.upper()} شروع شد")

                    # فقط اگر پوزیشن باز نداریم
                    if self.open_position:
                        print(f"   ⚠️  پوزیشن باز وجود دارد - منتظر بسته شدن")
                        self.was_in_overlap = False
                        continue

                    # از روند ذخیره شده استفاده کن
                    trend = self.overlap_trend
                    trend_strength = self.overlap_trend_strength

                    if trend and trend != 'neutral' and trend_strength >= config.MIN_PRICE_CHANGE:
                        print(f"   روند در overlap: {trend.upper()} ({trend_strength:.2f}%)")

                        # دریافت سوئینگ‌های سشن قبلی
                        previous_swings = self.swing_manager.get_previous_session_swings(current_session)
                        current_price = candle['close']

                        signal = None
                        target_swings = []

                        # استراتژی Counter-Trend - انتخاب همه سوئینگ‌های مناسب
                        if trend == 'bullish':
                            # روند صعودی در overlap بود → الان فروش
                            signal = 'sell'
                            print(f"   → سیگنال: SELL (counter-trend)")
                            # انتخاب همه سوئینگ lows که در محدوده فاصله مجاز هستند
                            target_swings = previous_swings['lows']
                        elif trend == 'bearish':
                            # روند نزولی در overlap بود → الان خرید
                            signal = 'buy'
                            print(f"   → سیگنال: BUY (counter-trend)")
                            # انتخاب همه سوئینگ highs که در محدوده فاصله مجاز هستند
                            target_swings = previous_swings['highs']

                        if target_swings:
                            # فیلتر کردن سوئینگ‌ها بر اساس فاصله و پیدا کردن نزدیک‌ترین
                            valid_swings = []
                            for swing in target_swings:
                                distance_pct = abs(swing['price'] - current_price) / current_price
                                if distance_pct <= config.MAX_TARGET_DISTANCE:
                                    swing['distance'] = abs(swing['price'] - current_price)
                                    valid_swings.append(swing)

                            if valid_swings:
                                # انتخاب نزدیک‌ترین سوئینگ
                                closest_swing = min(valid_swings, key=lambda x: x['distance'])

                                print(f"   📊 نزدیک‌ترین سوئینگ انتخاب شد")

                                # محاسبه استاپ لاس
                                stop_loss = self.calculate_stop_loss(
                                    current_price,
                                    signal,
                                    df.iloc[:idx+1]
                                )

                                # باز کردن یک پوزیشن
                                print(f"\n{'🟢 خرید' if signal == 'buy' else '🔴 فروش'} | "
                                      f"ورود: ${current_price:,.5f} | TP: ${closest_swing['price']:,.5f} | SL: ${stop_loss:,.5f}")

                                self.open_trade(
                                    signal,
                                    current_price,
                                    closest_swing['price'],
                                    stop_loss,
                                    current_session,
                                    trend,
                                    timestamp
                                )
                            else:
                                print(f"   ⚠️  همه تارگت‌ها خیلی دور هستند (>{config.MAX_TARGET_DISTANCE*100:.0f}%) - معامله نکن")

                    # ریست کردن وضعیت overlap
                    self.was_in_overlap = False
                    self.overlap_trend = None
                    self.overlap_trend_strength = 0

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


def main(symbol: str = None, days: int = 10):
    """
    تابع اصلی

    Args:
        symbol: نماد معاملاتی (پیش‌فرض: از config)
        days: تعداد روزهای گذشته
    """
    symbol = symbol or config.MARKET_SYMBOL

    print("🔬 بک‌تست استراتژی سوئینگ‌های سشن")
    print("=" * 80)
    print(f"📊 نماد: {symbol}")
    print(f"📅 دوره: {days} روز گذشته")
    print("=" * 80)

    # ایجاد نمونه
    backtest = SessionBacktest(initial_balance=1000.0, symbol=symbol)

    # دریافت داده‌های تاریخی
    df = backtest.fetch_historical_data(days=days)

    if df is None or len(df) == 0:
        print("❌ خطا در دریافت داده‌ها")
        return

    # اجرای بک‌تست
    backtest.run_backtest(df)

    # نمایش نتایج
    backtest.print_results()


if __name__ == "__main__":
    import sys

    # دریافت نماد از خط فرمان
    symbol = sys.argv[1] if len(sys.argv) > 1 else None
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    main(symbol=symbol, days=days)
