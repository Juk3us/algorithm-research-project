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
        self.open_positions = []  # چند پوزیشن (multi-lot)

        # آمار
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0

        # متغیرهای استراتژی: تشخیص روند در overlap و فازبندی
        self.was_in_overlap = False
        self.overlap_trend = None
        self.overlap_trend_strength = 0

        # Phase tracking: 'counter-trend' یا 'reversal'
        self.current_phase = 'counter-trend'
        self.phase1_complete = False  # آیا فاز 1 (counter-trend) تمام شد؟

        # تاریخچه سشن‌ها برای گرفتن swings از دو سشن قبل
        self.session_history = []  # هر کدام: {'session': 'tokyo', 'swings': {...}}

        # سوئینگ‌هایی که گرفته شده‌اند (captured)
        self.captured_swings = set()  # قیمت‌های سوئینگ‌هایی که به آنها رسیده‌ایم

        # راه‌اندازی صرافی/OANDA
        self.exchange = None
        self.oanda_api = None

        # اگر symbol جفت‌ارز فارکس است → سعی برای اتصال به OANDA
        if '/' in symbol and any(curr in symbol for curr in ['AUD', 'EUR', 'GBP', 'USD', 'JPY', 'CHF', 'CAD', 'NZD']):
            try:
                print(f"🔌 تلاش برای اتصال به OANDA برای {symbol}...")
                from oanda_api import OandaAPI

                # توکن OANDA
                oanda_token = 'dd81e6f027e604f8f213ee371aff985acb-91d76fd9d01e79cd02632684a06d7b89'
                self.oanda_api = OandaAPI(oanda_token, environment='practice')

                if self.oanda_api.test_connection():
                    print(f"✅ اتصال به OANDA برقرار شد")
                else:
                    print("⚠️  نتوانستیم به OANDA متصل شویم - استفاده از داده‌های شبیه‌سازی")
                    self.oanda_api = None
            except Exception as e:
                print(f"⚠️  خطا در اتصال به OANDA: {e}")
                print("⚠️  استفاده از داده‌های شبیه‌سازی شده")
                self.oanda_api = None
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

        # اگر OANDA متصل است، از OANDA API استفاده کن
        if self.oanda_api:
            try:
                # تبدیل symbol به فرمت OANDA (AUD/USD → AUD_USD)
                oanda_instrument = self.symbol.replace('/', '_')

                # محاسبه تعداد کندل‌ها (H1 = 24 کندل در روز)
                count = days * 24

                # دریافت داده‌ها از OANDA
                df = self.oanda_api.fetch_candles(oanda_instrument, 'H1', count)

                if df is not None and len(df) > 0:
                    return df
                else:
                    print("🔄 داده‌ای از OANDA دریافت نشد - استفاده از داده‌های شبیه‌سازی...")

            except Exception as e:
                print(f"⚠️  خطا در دریافت داده‌های OANDA: {e}")
                print("🔄 استفاده از داده‌های شبیه‌سازی شده...")

        # اگر صرافی کریپتو متصل است، از API استفاده کن
        elif self.exchange:
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

    def get_targets_from_previous_sessions(self, signal: str) -> List[float]:
        """
        دریافت تارگت‌ها از دو سشن قبلی

        Args:
            signal: 'buy' یا 'sell'

        Returns:
            لیست قیمت‌های تارگت (مرتب شده)
        """
        targets = []
        total_swings = 0
        filtered_swings = 0

        # بررسی دو سشن آخر
        sessions_to_check = self.session_history[-2:] if len(self.session_history) >= 2 else self.session_history

        for session_data in sessions_to_check:
            swings = session_data.get('swings', {})

            if signal == 'sell':
                # برای فروش: همه Lows (فقط اگر گرفته نشده باشند)
                swing_lows = swings.get('lows', [])
                for swing in swing_lows:
                    total_swings += 1
                    price = swing['price']
                    if price not in self.captured_swings:
                        targets.append(price)
                    else:
                        filtered_swings += 1
            else:  # buy
                # برای خرید: همه Highs (فقط اگر گرفته نشده باشند)
                swing_highs = swings.get('highs', [])
                for swing in swing_highs:
                    total_swings += 1
                    price = swing['price']
                    if price not in self.captured_swings:
                        targets.append(price)
                    else:
                        filtered_swings += 1

        if filtered_swings > 0:
            print(f"   🔍 فیلتر سوئینگ‌ها: {total_swings} کل → {len(targets)} باقی‌مانده ({filtered_swings} گرفته شده)")

        # مرتب‌سازی
        if signal == 'sell':
            # برای sell: از بالا به پایین (نزدیک‌ترین به دورترین)
            targets.sort(reverse=True)
        else:
            # برای buy: از پایین به بالا (نزدیک‌ترین به دورترین)
            targets.sort()

        return targets

    def calculate_stop_loss(self, entry_price: float, direction: str) -> float:
        """
        محاسبه استاپ لاس به صورت درصدی از قیمت ورود

        Args:
            entry_price: قیمت ورود
            direction: جهت معامله ('buy' یا 'sell')

        Returns:
            قیمت استاپ لاس
        """
        # Stop Loss درصدی (از config)
        stop_loss_pct = config.MAX_TRADE_RISK  # 5% = 0.05

        if direction == 'buy':
            # برای خرید: SL پایین‌تر از قیمت ورود
            stop_loss = entry_price * (1 - stop_loss_pct)
        else:  # sell
            # برای فروش: SL بالاتر از قیمت ورود
            stop_loss = entry_price * (1 + stop_loss_pct)

        return stop_loss

    def open_trade(self, signal: str, entry_price: float, targets: List[float],
                   stop_loss: float, session: str, trend: str, timestamp: pd.Timestamp, phase: str = 'counter-trend'):
        """
        باز کردن چند لات (یکی برای هر تارگت)

        Args:
            signal: 'buy' یا 'sell'
            entry_price: قیمت ورود
            targets: لیست قیمت‌های تارگت (مرتب شده)
            stop_loss: قیمت استاپ لاس (اگر None باشد، بدون SL)
            session: سشن فعلی
            trend: روند در overlap
            timestamp: زمان ورود
            phase: 'counter-trend' یا 'reversal'
        """
        if len(targets) == 0:
            print("   ⚠️  هیچ تارگتی یافت نشد - معامله باز نمی‌شود")
            return

        # محاسبه حجم کل بر اساس ریسک ثابت (بدون SL)
        # استفاده از 50% از موجودی برای کل معامله (بدون SL نیاز به سرمایه بیشتر)
        total_risk_amount = self.balance * 0.5

        # تبدیل به تعداد واحد (coin/token) بر اساس قیمت ورود
        total_position_size_in_coins = total_risk_amount / entry_price

        # تقسیم به چند لات
        num_lots = len(targets)
        lot_size = total_position_size_in_coins / num_lots

        if lot_size <= 0:
            return

        # باز کردن یک لات برای هر تارگت
        for i, target in enumerate(targets):
            if signal == 'buy':
                reward = target - entry_price
            else:  # sell
                reward = entry_price - target

            position = {
                'signal': signal,
                'entry_price': entry_price,
                'target_price': target,
                'stop_loss': stop_loss,  # None یا قیمت SL
                'position_size': lot_size,
                'lot_number': i + 1,
                'total_lots': num_lots,
                'entry_time': timestamp,
                'session': session,
                'trend': trend,
                'phase': phase,  # counter-trend یا reversal
                'reward': reward,
            }
            self.open_positions.append(position)

        sl_text = "بدون SL" if stop_loss is None else f"SL: ${stop_loss:,.5f}"
        print(f"\n{'🟢 خرید' if signal == 'buy' else '🔴 فروش'} | "
              f"فاز: {phase} | "
              f"ورود: ${entry_price:,.5f} | "
              f"تعداد لات: {num_lots} | "
              f"{sl_text}")
        print(f"   تارگت‌ها: {[f'${t:,.5f}' for t in targets]}")

    def check_position(self, current_candle: pd.Series):
        """
        بررسی همه پوزیشن‌های باز و بستن تدریجی

        Args:
            current_candle: کندل فعلی
        """
        if len(self.open_positions) == 0:
            return

        positions_to_close = []

        # بررسی هر لات
        for i, position in enumerate(self.open_positions):
            target_hit = False
            stop_hit = False
            timeout_close = False
            exit_price = None

            # بررسی timeout: اگر پوزیشن بیش از 48 ساعت باز بود، ببند
            time_open = (current_candle.name - position['entry_time']).total_seconds() / 3600  # ساعت
            if time_open > 48:  # 48 ساعت = 2 روز
                timeout_close = True
                exit_price = current_candle['close']
                print(f"   ⏱️  لات {position['lot_number']}/{position['total_lots']} timeout ({time_open:.1f}h) - بستن در ${exit_price:,.5f}")

            elif position['signal'] == 'buy':
                # بررسی target hit
                if current_candle['high'] >= position['target_price']:
                    target_hit = True
                    exit_price = position['target_price']
                # بررسی stop loss (فقط اگر SL تعریف شده باشد)
                elif position['stop_loss'] is not None and current_candle['low'] <= position['stop_loss']:
                    stop_hit = True
                    exit_price = position['stop_loss']
            else:  # sell
                # بررسی target hit
                if current_candle['low'] <= position['target_price']:
                    target_hit = True
                    exit_price = position['target_price']
                # بررسی stop loss (فقط اگر SL تعریف شده باشد)
                elif position['stop_loss'] is not None and current_candle['high'] >= position['stop_loss']:
                    stop_hit = True
                    exit_price = position['stop_loss']

            if target_hit or stop_hit or timeout_close:
                positions_to_close.append((i, exit_price, current_candle.name, target_hit))

        # بستن پوزیشن‌هایی که به تارگت یا SL رسیدند
        # از آخر به اول حذف می‌کنیم تا index ها قاطی نشوند
        for i, exit_price, exit_time, won in reversed(positions_to_close):
            self.close_single_lot(i, exit_price, exit_time, won)

    def close_single_lot(self, index: int, exit_price: float, exit_time: pd.Timestamp, won: bool):
        """
        بستن یک لات

        Args:
            index: شماره index لات در لیست
            exit_price: قیمت خروج
            exit_time: زمان خروج
            won: آیا به target رسید (True) یا SL خورد (False)
        """
        if index >= len(self.open_positions):
            return

        position = self.open_positions[index]

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
            # ثبت سوئینگ گرفته شده
            target_price = position['target_price']
            self.captured_swings.add(target_price)
            print(f"   📌 سوئینگ ${target_price:.5f} گرفته شد (کل: {len(self.captured_swings)})")
        else:
            self.losing_trades += 1
            self.total_loss += abs(pnl)

        # چاپ نتیجه
        result_emoji = "✅" if pnl > 0 else "❌"
        print(f"{result_emoji} لات {position['lot_number']}/{position['total_lots']} | "
              f"TP: ${exit_price:,.5f} | "
              f"P/L: ${pnl:,.2f} ({pnl_pct:.2f}%) | "
              f"موجودی: ${self.balance:,.2f}")

        # حذف لات از لیست
        phase_before_close = position['phase']
        signal_before_close = position['signal']

        del self.open_positions[index]

        # بررسی: آیا همه لات‌ها بسته شدند؟
        if len(self.open_positions) == 0:
            print(f"\n   ✅ همه لات‌ها بسته شدند (فاز {phase_before_close})")

            # اگر فاز counter-trend تمام شد، فاز reversal را شروع کن
            if phase_before_close == 'counter-trend' and won:
                print(f"   🔄 شروع فاز Reversal (معامله معکوس)")
                # سیگنال معکوس
                reversal_signal = 'buy' if signal_before_close == 'sell' else 'sell'
                # از همان نقطه ورود کن
                self.initiate_reversal_phase(reversal_signal, exit_price, exit_time)

    def initiate_reversal_phase(self, signal: str, entry_price: float, timestamp: pd.Timestamp):
        """
        شروع فاز reversal (معامله معکوس بعد از تمام شدن فاز counter-trend)

        Args:
            signal: 'buy' یا 'sell' (معکوس سیگنال قبلی)
            entry_price: قیمت ورود (همان نقطه خروج فاز 1)
            timestamp: زمان ورود
        """
        # گرفتن تارگت‌های معکوس
        targets = self.get_targets_from_previous_sessions(signal)

        if len(targets) == 0:
            print(f"   ⚠️  هیچ تارگتی برای فاز Reversal یافت نشد")
            return

        # فیلتر تارگت‌های صحیح بر اساس جهت معامله
        valid_targets = []
        for target in targets:
            # برای SELL: target باید پایین‌تر از قیمت ورود باشد
            # برای BUY: target باید بالاتر از قیمت ورود باشد
            if signal == 'sell' and target >= entry_price:
                continue
            if signal == 'buy' and target <= entry_price:
                continue

            # بررسی فاصله
            distance_pct = abs(target - entry_price) / entry_price
            if distance_pct <= config.MAX_TARGET_DISTANCE:
                valid_targets.append(target)

        if len(valid_targets) == 0:
            print(f"   ⚠️  هیچ تارگت صحیحی برای فاز Reversal یافت نشد")
            return

        # بدون Stop Loss
        stop_loss = None

        # باز کردن معامله reversal
        self.open_trade(
            signal=signal,
            entry_price=entry_price,
            targets=valid_targets,
            stop_loss=stop_loss,
            session='reversal',
            trend='reversal',
            timestamp=timestamp,
            phase='reversal'
        )

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

                    # ذخیره swings در تاریخچه
                    if current_session in self.swing_manager.session_swings:
                        swings = self.swing_manager.session_swings[current_session]
                        self.session_history.append({
                            'session': current_session,
                            'swings': swings
                        })
                        # نگه داشتن فقط 3 سشن آخر
                        if len(self.session_history) > 3:
                            self.session_history.pop(0)

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

            # بررسی پوزیشن‌های باز
            if len(self.open_positions) > 0:
                self.check_position(candle)

            # اگر پوزیشن باز نداریم، به دنبال سیگنال باش
            if len(self.open_positions) == 0:
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
                    if len(self.open_positions) > 0:
                        print(f"   ⚠️  پوزیشن باز وجود دارد - منتظر بسته شدن")
                        self.was_in_overlap = False
                        continue

                    # از روند ذخیره شده استفاده کن
                    trend = self.overlap_trend
                    trend_strength = self.overlap_trend_strength

                    if trend and trend != 'neutral' and trend_strength >= config.MIN_PRICE_CHANGE:
                        print(f"   روند در overlap: {trend.upper()} ({trend_strength:.2f}%)")

                        current_price = candle['close']
                        signal = None

                        # تعیین سیگنال
                        if trend == 'bullish':
                            signal = 'sell'
                            print(f"   → سیگنال: SELL (counter-trend)")
                        elif trend == 'bearish':
                            signal = 'buy'
                            print(f"   → سیگنال: BUY (counter-trend)")

                        if signal:
                            # دریافت تارگت‌ها از دو سشن قبلی
                            targets = self.get_targets_from_previous_sessions(signal)

                            if len(targets) > 0:
                                # فیلتر تارگت‌های صحیح بر اساس جهت معامله
                                valid_targets = []
                                for target in targets:
                                    # برای SELL: target باید پایین‌تر از قیمت ورود باشد
                                    # برای BUY: target باید بالاتر از قیمت ورود باشد
                                    if signal == 'sell' and target >= current_price:
                                        continue  # skip این target
                                    if signal == 'buy' and target <= current_price:
                                        continue  # skip این target

                                    # بررسی فاصله
                                    distance_pct = abs(target - current_price) / current_price
                                    if distance_pct <= config.MAX_TARGET_DISTANCE:
                                        valid_targets.append(target)

                                if len(valid_targets) > 0:
                                    print(f"   📊 {len(valid_targets)} تارگت یافت شد")

                                    # بدون Stop Loss
                                    stop_loss = None

                                    # باز کردن معامله با چند لات
                                    self.open_trade(
                                        signal=signal,
                                        entry_price=current_price,
                                        targets=valid_targets,
                                        stop_loss=stop_loss,
                                        session=current_session,
                                        trend=trend,
                                        timestamp=timestamp,
                                        phase='counter-trend'
                                    )
                                else:
                                    print(f"   ⚠️  همه تارگت‌ها خیلی دور هستند (>{config.MAX_TARGET_DISTANCE*100:.0f}%) - معامله نکن")
                            else:
                                print(f"   ⚠️  هیچ تارگتی در دو سشن قبلی یافت نشد")

                    # ریست کردن وضعیت overlap
                    self.was_in_overlap = False
                    self.overlap_trend = None
                    self.overlap_trend_strength = 0

        # بستن سشن آخر
        if current_session and len(session_data) > 0:
            session_df = pd.DataFrame.from_dict(session_data, orient='index')
            self.swing_manager.update_session_swings(current_session, session_df)

            # ذخیره swings در تاریخچه
            if current_session in self.swing_manager.session_swings:
                swings = self.swing_manager.session_swings[current_session]
                self.session_history.append({
                    'session': current_session,
                    'swings': swings
                })

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
