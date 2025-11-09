"""
ربات معاملاتی اتوماتیک بر اساس سشن‌های جهانی
Automated Trading Bot Based on Global Trading Sessions
"""

import ccxt
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

import config
from session_manager import SessionManager
from risk_manager import RiskManager
from swing_detector import SwingDetector


# تنظیمات لاگ
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingBot:
    """ربات معاملاتی خودکار"""

    def __init__(self):
        """مقداردهی اولیه ربات"""
        logger.info("=" * 70)
        logger.info("راه‌اندازی ربات معاملاتی")
        logger.info("=" * 70)

        # مدیریت سشن‌ها، ریسک و تحلیل سوئینگ
        self.session_manager = SessionManager()
        self.risk_manager = RiskManager()
        self.swing_detector = SwingDetector()

        # راه‌اندازی صرافی
        self.exchange = self._init_exchange()

        # پوزیشن‌های باز
        self.open_positions = []

        # حالت آزمایشی
        self.test_mode = config.TEST_MODE
        if self.test_mode:
            logger.warning("⚠️  ربات در حالت آزمایشی اجرا می‌شود - معاملات واقعی انجام نمی‌شود")
            if config.PAPER_TRADING:
                self.paper_balance = config.INITIAL_PAPER_BALANCE
                logger.info(f"موجودی اولیه معامله کاغذی: ${self.paper_balance:,.2f}")

        logger.info("✓ ربات با موفقیت راه‌اندازی شد")

    def _init_exchange(self) -> ccxt.Exchange:
        """راه‌اندازی صرافی"""
        try:
            exchange_class = getattr(ccxt, config.EXCHANGE_NAME)
            exchange = exchange_class({
                'apiKey': config.API_KEY,
                'secret': config.API_SECRET,
                'password': config.API_PASSWORD if hasattr(config, 'API_PASSWORD') else None,
                'enableRateLimit': True,
            })

            # تست اتصال
            if not config.TEST_MODE:
                exchange.load_markets()
                logger.info(f"✓ اتصال به صرافی {config.EXCHANGE_NAME} برقرار شد")
            else:
                logger.info(f"⚠️  حالت آزمایشی - اتصال واقعی به صرافی برقرار نشد")

            return exchange

        except Exception as e:
            logger.error(f"خطا در اتصال به صرافی: {str(e)}")
            raise

    def get_balance(self, currency: str = config.BASE_CURRENCY) -> float:
        """
        دریافت موجودی

        Args:
            currency: نوع ارز

        Returns:
            موجودی
        """
        if config.PAPER_TRADING:
            return self.paper_balance

        try:
            balance = self.exchange.fetch_balance()
            return balance['total'].get(currency, 0)
        except Exception as e:
            logger.error(f"خطا در دریافت موجودی: {str(e)}")
            return 0

    def fetch_ohlcv(self, symbol: str = config.MARKET_SYMBOL,
                    timeframe: str = config.CHART_TIMEFRAME,
                    limit: int = 100) -> Optional[pd.DataFrame]:
        """
        دریافت داده‌های OHLCV

        Args:
            symbol: نماد معاملاتی
            timeframe: تایم فریم
            limit: تعداد کندل

        Returns:
            DataFrame یا None
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df

        except ccxt.NetworkError as e:
            logger.error(f"خطای شبکه در دریافت داده: {str(e)}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"خطای صرافی در دریافت داده: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"خطای ناشناخته در دریافت داده: {str(e)}")
            return None

    def analyze_market(self, df: pd.DataFrame, overlap_info: Dict) -> Tuple[Optional[str], Optional[Dict]]:
        """
        تحلیل بازار و تشخیص سیگنال بر اساس تاچ سوئینگ‌های قبلی

        استراتژی: تمام سوئینگ‌ها یک بار دیگر تاچ می‌شوند
        - تاچ Higher High → فروش
        - تاچ Lower Low → خرید

        Args:
            df: DataFrame حاوی داده‌های قیمت
            overlap_info: اطلاعات همپوشانی فعال

        Returns:
            (سیگنال: 'buy', 'sell' یا None, اطلاعات سوئینگ)
        """
        if df is None or len(df) < config.MIN_CANDLES:
            logger.debug("تعداد کندل کافی نیست")
            return None, None

        # تولید سیگنال با استفاده از swing detector
        signal, swing_info = self.swing_detector.generate_trading_signal(df)

        if signal and swing_info:
            logger.info("=" * 70)
            if signal == 'buy':
                logger.info(f"🟢 سیگنال خرید")
            else:
                logger.info(f"🔴 سیگنال فروش")
            logger.info(f"   دلیل: {swing_info['reason']}")
            logger.info(f"   سطح سوئینگ: ${swing_info['swing_level']:,.2f}")
            logger.info(f"   قیمت فعلی: ${swing_info['current_price']:,.2f}")
            logger.info(f"   قدرت سوئینگ: {swing_info['strength']:.2f}%")
            logger.info("=" * 70)

        return signal, swing_info

    def execute_trade(self, signal: str, df: pd.DataFrame) -> bool:
        """
        اجرای معامله

        Args:
            signal: سیگنال معاملاتی ('buy' یا 'sell')
            df: DataFrame حاوی داده‌های قیمت

        Returns:
            True اگر معامله موفق بود
        """
        try:
            # دریافت قیمت فعلی
            current_price = df['close'].iloc[-1]

            # دریافت موجودی
            balance = self.get_balance()
            self.risk_manager.update_balance(balance)

            # بررسی امکان معامله
            can_trade, reason = self.risk_manager.can_trade(balance)
            if not can_trade:
                logger.warning(f"⚠️  امکان معامله وجود ندارد: {reason}")
                return False

            # بررسی تعداد پوزیشن‌های باز
            if len(self.open_positions) >= config.MAX_OPEN_POSITIONS:
                logger.warning(f"⚠️  تعداد پوزیشن‌های باز به حداکثر ({config.MAX_OPEN_POSITIONS}) رسیده")
                return False

            # محاسبه ATR
            atr = self.risk_manager.calculate_atr(df)

            # محاسبه استاپ لاس
            stop_loss = self.risk_manager.calculate_stop_loss(current_price, signal, atr)

            # محاسبه تیک پرافیت
            take_profit = self.risk_manager.calculate_take_profit(current_price, stop_loss, signal)

            # محاسبه اندازه پوزیشن
            position_size = self.risk_manager.calculate_position_size(balance, current_price, stop_loss)

            if position_size <= 0:
                logger.warning("⚠️  اندازه پوزیشن نامعتبر")
                return False

            # ارزش پوزیشن
            position_value = position_size * current_price

            # اطلاعات معامله
            trade_info = {
                'timestamp': datetime.now(),
                'signal': signal,
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': position_size,
                'position_value': position_value,
                'status': 'open'
            }

            logger.info("=" * 70)
            logger.info(f"{'خرید' if signal == 'buy' else 'فروش'} {config.MARKET_SYMBOL}")
            logger.info("-" * 70)
            logger.info(f"قیمت ورود: ${current_price:,.2f}")
            logger.info(f"استاپ لاس: ${stop_loss:,.2f}")
            logger.info(f"تیک پرافیت: ${take_profit:,.2f}")
            logger.info(f"اندازه پوزیشن: {position_size:.8f}")
            logger.info(f"ارزش پوزیشن: ${position_value:,.2f}")
            logger.info("=" * 70)

            # اجرای معامله
            if config.TEST_MODE or config.PAPER_TRADING:
                logger.info("⚠️  حالت آزمایشی - سفارش واقعی ثبت نشد")
                self.open_positions.append(trade_info)
                return True
            else:
                # ثبت سفارش واقعی
                order_type = 'market'
                side = signal  # 'buy' or 'sell'

                order = self.exchange.create_order(
                    symbol=config.MARKET_SYMBOL,
                    type=order_type,
                    side=side,
                    amount=position_size
                )

                logger.info(f"✓ سفارش ثبت شد - شناسه: {order['id']}")
                trade_info['order_id'] = order['id']
                self.open_positions.append(trade_info)

                return True

        except Exception as e:
            logger.error(f"خطا در اجرای معامله: {str(e)}")
            return False

    def check_open_positions(self):
        """بررسی و مدیریت پوزیشن‌های باز"""
        if not self.open_positions:
            return

        # دریافت قیمت فعلی
        df = self.fetch_ohlcv(limit=1)
        if df is None:
            return

        current_price = df['close'].iloc[-1]

        for position in self.open_positions[:]:  # کپی لیست برای تغییر همزمان
            if position['status'] != 'open':
                continue

            entry_price = position['entry_price']
            stop_loss = position['stop_loss']
            take_profit = position['take_profit']
            signal = position['signal']

            # بررسی استاپ لاس
            if signal == 'buy' and current_price <= stop_loss:
                self._close_position(position, current_price, 'stop_loss')
            elif signal == 'sell' and current_price >= stop_loss:
                self._close_position(position, current_price, 'stop_loss')

            # بررسی تیک پرافیت
            elif signal == 'buy' and current_price >= take_profit:
                self._close_position(position, current_price, 'take_profit')
            elif signal == 'sell' and current_price <= take_profit:
                self._close_position(position, current_price, 'take_profit')

            # بررسی trailing stop
            elif config.USE_TRAILING_STOP:
                self._check_trailing_stop(position, current_price)

    def _close_position(self, position: Dict, exit_price: float, reason: str):
        """
        بستن پوزیشن

        Args:
            position: اطلاعات پوزیشن
            exit_price: قیمت خروج
            reason: دلیل بسته شدن
        """
        try:
            position['exit_price'] = exit_price
            position['exit_time'] = datetime.now()
            position['close_reason'] = reason
            position['status'] = 'closed'

            # محاسبه سود/ضرر
            if position['signal'] == 'buy':
                profit_loss = (exit_price - position['entry_price']) * position['position_size']
            else:  # sell
                profit_loss = (position['entry_price'] - exit_price) * position['position_size']

            position['profit_loss'] = profit_loss

            # ثبت نتیجه معامله
            self.risk_manager.record_trade(profit_loss)

            # به‌روزرسانی موجودی کاغذی
            if config.PAPER_TRADING:
                self.paper_balance += profit_loss

            logger.info("=" * 70)
            logger.info(f"بستن پوزیشن - {reason}")
            logger.info("-" * 70)
            logger.info(f"قیمت ورود: ${position['entry_price']:,.2f}")
            logger.info(f"قیمت خروج: ${exit_price:,.2f}")
            logger.info(f"سود/ضرر: ${profit_loss:,.2f}")
            logger.info("=" * 70)

            # حذف از لیست پوزیشن‌های باز
            self.open_positions.remove(position)

        except Exception as e:
            logger.error(f"خطا در بستن پوزیشن: {str(e)}")

    def _check_trailing_stop(self, position: Dict, current_price: float):
        """
        بررسی و به‌روزرسانی trailing stop

        Args:
            position: اطلاعات پوزیشن
            current_price: قیمت فعلی
        """
        signal = position['signal']
        entry_price = position['entry_price']

        # محاسبه trailing stop جدید
        if signal == 'buy':
            # در خرید، اگر قیمت بالا رفته trailing stop را بالا می‌بریم
            potential_stop = current_price * (1 - config.TRAILING_STOP_PERCENTAGE)
            if potential_stop > position['stop_loss']:
                position['stop_loss'] = potential_stop
                logger.debug(f"Trailing stop به‌روز شد: ${potential_stop:,.2f}")
        else:  # sell
            # در فروش، اگر قیمت پایین آمده trailing stop را پایین می‌بریم
            potential_stop = current_price * (1 + config.TRAILING_STOP_PERCENTAGE)
            if potential_stop < position['stop_loss']:
                position['stop_loss'] = potential_stop
                logger.debug(f"Trailing stop به‌روز شد: ${potential_stop:,.2f}")

    def run_once(self):
        """اجرای یک چرخه کامل ربات"""
        try:
            # بررسی سشن‌ها
            should_trade, overlap_info = self.session_manager.should_trade()

            if should_trade:
                logger.info(f"📍 همپوشانی فعال: {overlap_info['name']}")

                # دریافت داده‌های بازار
                df = self.fetch_ohlcv()

                if df is not None:
                    # تحلیل بازار
                    signal, swing_info = self.analyze_market(df, overlap_info)

                    # اجرای معامله
                    if signal and swing_info:
                        self.execute_trade(signal, df)
                    else:
                        logger.debug("سیگنال معاملاتی پیدا نشد (هیچ سوئینگی تاچ نشده)")
            else:
                logger.debug("خارج از زمان همپوشانی سشن‌ها")

            # بررسی پوزیشن‌های باز
            self.check_open_positions()

        except Exception as e:
            logger.error(f"خطا در اجرای ربات: {str(e)}")

    def run(self):
        """اجرای مداوم ربات"""
        logger.info("\n🚀 شروع اجرای ربات معاملاتی")
        logger.info(f"بررسی هر {config.CHECK_INTERVAL} ثانیه\n")

        try:
            while True:
                # نمایش وضعیت سشن‌ها (هر ساعت یک بار)
                current_minute = datetime.now().minute
                if current_minute == 0:
                    self.session_manager.print_status()
                    self.risk_manager.print_statistics()

                # اجرای چرخه
                self.run_once()

                # انتظار تا چرخه بعدی
                time.sleep(config.CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\n🛑 توقف ربات توسط کاربر")
            self._shutdown()

        except Exception as e:
            logger.error(f"خطای غیرمنتظره: {str(e)}")
            self._shutdown()

    def _shutdown(self):
        """خاموش کردن ربات"""
        logger.info("\n" + "=" * 70)
        logger.info("خاموش کردن ربات")
        logger.info("=" * 70)

        # بستن پوزیشن‌های باز (اختیاری)
        if self.open_positions:
            logger.warning(f"⚠️  {len(self.open_positions)} پوزیشن باز وجود دارد")

        # نمایش آمار نهایی
        self.risk_manager.print_statistics()

        logger.info("✓ ربات با موفقیت خاموش شد")


# تست مستقل ماژول
if __name__ == "__main__":
    bot = TradingBot()
    bot.session_manager.print_status()
    bot.run_once()
