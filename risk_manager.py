"""
مدیریت ریسک و محاسبات مربوط به معاملات
Risk Management and Trade Calculations
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import pandas as pd
import config


class RiskManager:
    """مدیریت ریسک و محاسبه اندازه معاملات"""

    def __init__(self):
        """مقداردهی اولیه مدیر ریسک"""
        # ردیابی ضرر و زیان
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.monthly_loss = 0.0

        # زمان آخرین بازنشانی
        self.last_daily_reset = datetime.now().date()
        self.last_weekly_reset = datetime.now().isocalendar()[1]  # شماره هفته
        self.last_monthly_reset = datetime.now().month

        # ردیابی معاملات
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

        # موجودی اولیه (برای محاسبه درصد)
        self.initial_balance = 0.0
        self.current_balance = 0.0

    def reset_if_needed(self):
        """بازنشانی ضرر و زیان در صورت شروع دوره جدید"""
        now = datetime.now()

        # بازنشانی روزانه
        if now.date() > self.last_daily_reset:
            self.daily_loss = 0.0
            self.last_daily_reset = now.date()

        # بازنشانی هفتگی
        current_week = now.isocalendar()[1]
        if current_week != self.last_weekly_reset:
            self.weekly_loss = 0.0
            self.last_weekly_reset = current_week

        # بازنشانی ماهانه
        if now.month != self.last_monthly_reset:
            self.monthly_loss = 0.0
            self.last_monthly_reset = now.month

    def update_balance(self, balance: float):
        """
        به‌روزرسانی موجودی

        Args:
            balance: موجودی فعلی
        """
        if self.initial_balance == 0:
            self.initial_balance = balance

        self.current_balance = balance

    def calculate_position_size(self, balance: float, entry_price: float,
                                stop_loss_price: float) -> float:
        """
        محاسبه اندازه پوزیشن بر اساس ریسک

        Args:
            balance: موجودی فعلی
            entry_price: قیمت ورود
            stop_loss_price: قیمت استاپ لاس

        Returns:
            اندازه پوزیشن (مقدار ارز)
        """
        # محاسبه مقدار ریسک بر اساس موجودی
        risk_amount = balance * config.MAX_TRADE_RISK

        # محاسبه فاصله تا استاپ لاس
        stop_loss_distance = abs(entry_price - stop_loss_price)

        if stop_loss_distance == 0:
            return 0

        # محاسبه اندازه پوزیشن
        position_size = risk_amount / stop_loss_distance

        return position_size

    def calculate_stop_loss(self, entry_price: float, direction: str,
                           atr: Optional[float] = None) -> float:
        """
        محاسبه قیمت استاپ لاس

        Args:
            entry_price: قیمت ورود
            direction: جهت معامله ('buy' یا 'sell')
            atr: مقدار ATR (اختیاری)

        Returns:
            قیمت استاپ لاس
        """
        if config.USE_ATR_STOP_LOSS and atr is not None:
            # استفاده از ATR برای محاسبه استاپ لاس
            stop_distance = atr * config.ATR_MULTIPLIER
        else:
            # استفاده از درصد ثابت
            stop_distance = entry_price * config.STOP_LOSS_RISK

        if direction == 'buy':
            stop_loss = entry_price - stop_distance
        else:  # sell
            stop_loss = entry_price + stop_distance

        return stop_loss

    def calculate_take_profit(self, entry_price: float, stop_loss_price: float,
                             direction: str) -> float:
        """
        محاسبه قیمت تیک پرافیت بر اساس نسبت ریسک/ریوارد

        Args:
            entry_price: قیمت ورود
            stop_loss_price: قیمت استاپ لاس
            direction: جهت معامله ('buy' یا 'sell')

        Returns:
            قیمت تیک پرافیت
        """
        risk_distance = abs(entry_price - stop_loss_price)
        reward_distance = risk_distance * config.RISK_REWARD_RATIO

        if direction == 'buy':
            take_profit = entry_price + reward_distance
        else:  # sell
            take_profit = entry_price - reward_distance

        return take_profit

    def can_trade(self, balance: float) -> Tuple[bool, str]:
        """
        بررسی امکان انجام معامله جدید

        Args:
            balance: موجودی فعلی

        Returns:
            (امکان معامله, دلیل عدم امکان)
        """
        # بازنشانی در صورت نیاز
        self.reset_if_needed()

        # بررسی موجودی کافی
        if balance < config.MIN_BALANCE:
            return False, f"موجودی کافی نیست (حداقل: {config.MIN_BALANCE} USDT)"

        # محاسبه ضرر به عنوان درصد از موجودی فعلی
        daily_loss_pct = self.daily_loss / balance if balance > 0 else 0
        weekly_loss_pct = self.weekly_loss / balance if balance > 0 else 0
        monthly_loss_pct = self.monthly_loss / balance if balance > 0 else 0

        # بررسی محدودیت ضرر روزانه
        if daily_loss_pct >= config.DAILY_STOP_LOSS:
            return False, f"محدودیت ضرر روزانه ({config.DAILY_STOP_LOSS * 100}%) به پایان رسیده"

        # بررسی محدودیت ضرر هفتگی
        if weekly_loss_pct >= config.WEEKLY_STOP_LOSS:
            return False, f"محدودیت ضرر هفتگی ({config.WEEKLY_STOP_LOSS * 100}%) به پایان رسیده"

        # بررسی محدودیت ضرر ماهانه
        if monthly_loss_pct >= config.MONTHLY_STOP_LOSS:
            return False, f"محدودیت ضرر ماهانه ({config.MONTHLY_STOP_LOSS * 100}%) به پایان رسیده"

        return True, "OK"

    def record_trade(self, profit_loss: float):
        """
        ثبت نتیجه معامله

        Args:
            profit_loss: سود یا ضرر (منفی = ضرر، مثبت = سود)
        """
        self.total_trades += 1

        if profit_loss > 0:
            self.winning_trades += 1
        elif profit_loss < 0:
            self.losing_trades += 1
            # ثبت ضرر
            loss_amount = abs(profit_loss)
            self.daily_loss += loss_amount
            self.weekly_loss += loss_amount
            self.monthly_loss += loss_amount

    def calculate_atr(self, df: pd.DataFrame, period: int = config.ATR_PERIOD) -> float:
        """
        محاسبه ATR (Average True Range)

        Args:
            df: DataFrame شامل ستون‌های high, low, close
            period: دوره محاسبه ATR

        Returns:
            مقدار ATR
        """
        if len(df) < period + 1:
            return 0

        # محاسبه True Range
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # محاسبه ATR
        atr = true_range.rolling(window=period).mean().iloc[-1]

        return atr

    def get_statistics(self) -> Dict:
        """
        دریافت آمار کلی

        Returns:
            دیکشنری حاوی آمار
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'daily_loss': self.daily_loss,
            'weekly_loss': self.weekly_loss,
            'monthly_loss': self.monthly_loss,
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'profit_loss': self.current_balance - self.initial_balance if self.initial_balance > 0 else 0
        }

    def print_statistics(self):
        """چاپ آمار معاملات"""
        stats = self.get_statistics()

        print("\n" + "=" * 70)
        print("آمار مدیریت ریسک".center(70))
        print("=" * 70)

        print(f"\n💰 موجودی:")
        print(f"   موجودی اولیه: ${stats['initial_balance']:,.2f}")
        print(f"   موجودی فعلی: ${stats['current_balance']:,.2f}")
        print(f"   سود/ضرر کل: ${stats['profit_loss']:,.2f}")

        print(f"\n📊 معاملات:")
        print(f"   تعداد کل: {stats['total_trades']}")
        print(f"   معاملات سودده: {stats['winning_trades']}")
        print(f"   معاملات ضررده: {stats['losing_trades']}")
        print(f"   نرخ برد: {stats['win_rate']:.1f}%")

        print(f"\n📉 ضرر و زیان:")
        balance = stats['current_balance'] if stats['current_balance'] > 0 else 1
        print(f"   ضرر روزانه: ${stats['daily_loss']:,.2f} ({stats['daily_loss'] / balance * 100:.2f}%)")
        print(f"   ضرر هفتگی: ${stats['weekly_loss']:,.2f} ({stats['weekly_loss'] / balance * 100:.2f}%)")
        print(f"   ضرر ماهانه: ${stats['monthly_loss']:,.2f} ({stats['monthly_loss'] / balance * 100:.2f}%)")

        print(f"\n⚠️  محدودیت‌ها:")
        print(f"   حداکثر ضرر روزانه: {config.DAILY_STOP_LOSS * 100}%")
        print(f"   حداکثر ضرر هفتگی: {config.WEEKLY_STOP_LOSS * 100}%")
        print(f"   حداکثر ضرر ماهانه: {config.MONTHLY_STOP_LOSS * 100}%")

        can_trade, reason = self.can_trade(stats['current_balance'])
        print(f"\n✓ وضعیت معامله:")
        if can_trade:
            print(f"   ✓ امکان معامله وجود دارد")
        else:
            print(f"   ✗ امکان معامله وجود ندارد: {reason}")

        print("=" * 70 + "\n")


# تست مستقل ماژول
if __name__ == "__main__":
    print("تست مدیریت ریسک")
    print("-" * 70)

    # ایجاد نمونه
    rm = RiskManager()

    # تنظیم موجودی اولیه
    initial_balance = 1000.0
    rm.update_balance(initial_balance)

    print(f"\nموجودی اولیه: ${initial_balance:,.2f}\n")

    # تست محاسبه پوزیشن
    entry_price = 50000.0
    stop_loss = rm.calculate_stop_loss(entry_price, 'buy')
    position_size = rm.calculate_position_size(initial_balance, entry_price, stop_loss)
    take_profit = rm.calculate_take_profit(entry_price, stop_loss, 'buy')

    print(f"قیمت ورود: ${entry_price:,.2f}")
    print(f"استاپ لاس: ${stop_loss:,.2f}")
    print(f"تیک پرافیت: ${take_profit:,.2f}")
    print(f"اندازه پوزیشن: {position_size:.8f} BTC")
    print(f"ارزش پوزیشن: ${position_size * entry_price:,.2f}")

    # تست ثبت معاملات
    print("\n" + "-" * 70)
    print("شبیه‌سازی معاملات:")
    print("-" * 70)

    # معامله اول - سود
    rm.record_trade(50)
    rm.update_balance(initial_balance + 50)
    print("معامله 1: +$50 (سود)")

    # معامله دوم - ضرر
    rm.record_trade(-30)
    rm.update_balance(initial_balance + 50 - 30)
    print("معامله 2: -$30 (ضرر)")

    # معامله سوم - سود
    rm.record_trade(40)
    rm.update_balance(initial_balance + 50 - 30 + 40)
    print("معامله 3: +$40 (سود)")

    # نمایش آمار
    rm.print_statistics()

    # تست محدودیت‌ها
    print("\nتست محدودیت ضرر:")
    print("-" * 70)

    # ثبت ضرر سنگین
    rm.daily_loss = initial_balance * 0.08  # 8% ضرر روزانه
    can_trade, reason = rm.can_trade(rm.current_balance)
    print(f"ضرر روزانه 8%: {reason}")
