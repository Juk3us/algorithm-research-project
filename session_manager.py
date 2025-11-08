"""
مدیریت سشن‌های معاملاتی و زمان‌های همپوشانی
Trading Session Manager with Overlap Detection
"""

from datetime import datetime, time
import pytz
from typing import Dict, List, Tuple, Optional
import config


class SessionManager:
    """مدیریت سشن‌های معاملاتی و تشخیص همپوشانی‌ها"""

    def __init__(self, timezone: str = config.TIMEZONE):
        """
        مقداردهی اولیه مدیر سشن

        Args:
            timezone: منطقه زمانی (پیش‌فرض: تهران)
        """
        self.timezone = pytz.timezone(timezone)
        self.sessions = self._parse_sessions(config.TRADING_SESSIONS)
        self.overlaps = self._parse_overlaps(config.SESSION_OVERLAPS)

    def _parse_time(self, time_str: str) -> time:
        """تبدیل رشته زمان به شیء time"""
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)

    def _parse_sessions(self, sessions_config: Dict) -> Dict:
        """پردازش تنظیمات سشن‌ها"""
        parsed = {}
        for session_key, session_data in sessions_config.items():
            parsed[session_key] = {
                'name': session_data['name'],
                'open': self._parse_time(session_data['open']),
                'close': self._parse_time(session_data['close']),
                'gmt_offset': session_data['gmt_offset']
            }
        return parsed

    def _parse_overlaps(self, overlaps_config: Dict) -> Dict:
        """پردازش تنظیمات همپوشانی‌ها"""
        parsed = {}
        for overlap_key, overlap_data in overlaps_config.items():
            parsed[overlap_key] = {
                'name': overlap_data['name'],
                'start': self._parse_time(overlap_data['start']),
                'end': self._parse_time(overlap_data['end']),
                'priority': overlap_data['priority']
            }
        return parsed

    def is_time_in_range(self, current_time: time, start_time: time,
                         end_time: time) -> bool:
        """
        بررسی قرار گرفتن زمان در بازه مشخص

        Args:
            current_time: زمان فعلی
            start_time: زمان شروع
            end_time: زمان پایان

        Returns:
            True اگر زمان در بازه باشد
        """
        if start_time <= end_time:
            # بازه عادی (در یک روز)
            return start_time <= current_time < end_time
        else:
            # بازه که از نیمه شب عبور می‌کند
            return current_time >= start_time or current_time < end_time

    def get_current_time(self) -> datetime:
        """دریافت زمان فعلی در منطقه زمانی تنظیم شده"""
        return datetime.now(self.timezone)

    def is_session_active(self, session_key: str,
                         current_time: Optional[datetime] = None) -> bool:
        """
        بررسی فعال بودن یک سشن معاملاتی

        Args:
            session_key: کلید سشن (tokyo, london, newyork)
            current_time: زمان مورد بررسی (پیش‌فرض: زمان فعلی)

        Returns:
            True اگر سشن فعال باشد
        """
        if current_time is None:
            current_time = self.get_current_time()

        if session_key not in self.sessions:
            return False

        session = self.sessions[session_key]
        current_time_only = current_time.time()

        return self.is_time_in_range(
            current_time_only,
            session['open'],
            session['close']
        )

    def get_active_sessions(self,
                           current_time: Optional[datetime] = None) -> List[str]:
        """
        دریافت لیست سشن‌های فعال

        Args:
            current_time: زمان مورد بررسی (پیش‌فرض: زمان فعلی)

        Returns:
            لیست کلیدهای سشن‌های فعال
        """
        if current_time is None:
            current_time = self.get_current_time()

        active = []
        for session_key in self.sessions.keys():
            if self.is_session_active(session_key, current_time):
                active.append(session_key)

        return active

    def is_overlap_active(self, overlap_key: str,
                         current_time: Optional[datetime] = None) -> bool:
        """
        بررسی فعال بودن یک همپوشانی

        Args:
            overlap_key: کلید همپوشانی
            current_time: زمان مورد بررسی (پیش‌فرض: زمان فعلی)

        Returns:
            True اگر همپوشانی فعال باشد
        """
        if current_time is None:
            current_time = self.get_current_time()

        if overlap_key not in self.overlaps:
            return False

        overlap = self.overlaps[overlap_key]
        current_time_only = current_time.time()

        return self.is_time_in_range(
            current_time_only,
            overlap['start'],
            overlap['end']
        )

    def get_active_overlaps(self,
                           current_time: Optional[datetime] = None) -> List[Dict]:
        """
        دریافت لیست همپوشانی‌های فعال (مرتب شده بر اساس اولویت)

        Args:
            current_time: زمان مورد بررسی (پیش‌فرض: زمان فعلی)

        Returns:
            لیست همپوشانی‌های فعال با اطلاعات کامل
        """
        if current_time is None:
            current_time = self.get_current_time()

        active_overlaps = []
        for overlap_key, overlap_data in self.overlaps.items():
            if self.is_overlap_active(overlap_key, current_time):
                active_overlaps.append({
                    'key': overlap_key,
                    'name': overlap_data['name'],
                    'priority': overlap_data['priority'],
                    'start': overlap_data['start'],
                    'end': overlap_data['end']
                })

        # مرتب‌سازی بر اساس اولویت (بالاترین اولویت اول)
        active_overlaps.sort(key=lambda x: x['priority'], reverse=True)

        return active_overlaps

    def get_highest_priority_overlap(self,
                                     current_time: Optional[datetime] = None) -> Optional[Dict]:
        """
        دریافت همپوشانی با بالاترین اولویت

        Args:
            current_time: زمان مورد بررسی (پیش‌فرض: زمان فعلی)

        Returns:
            همپوشانی با بالاترین اولویت یا None
        """
        active_overlaps = self.get_active_overlaps(current_time)
        return active_overlaps[0] if active_overlaps else None

    def should_trade(self, current_time: Optional[datetime] = None) -> Tuple[bool, Optional[Dict]]:
        """
        تصمیم‌گیری برای معامله بر اساس همپوشانی‌های فعال

        Args:
            current_time: زمان مورد بررسی (پیش‌فرض: زمان فعلی)

        Returns:
            (آیا باید معامله کرد, اطلاعات همپوشانی)
        """
        highest_priority = self.get_highest_priority_overlap(current_time)

        if highest_priority:
            return True, highest_priority
        else:
            return False, None

    def get_session_info(self, session_key: str) -> Optional[Dict]:
        """
        دریافت اطلاعات یک سشن

        Args:
            session_key: کلید سشن

        Returns:
            اطلاعات سشن یا None
        """
        if session_key not in self.sessions:
            return None

        session = self.sessions[session_key]
        is_active = self.is_session_active(session_key)

        return {
            'key': session_key,
            'name': session['name'],
            'open': session['open'].strftime('%H:%M'),
            'close': session['close'].strftime('%H:%M'),
            'is_active': is_active
        }

    def get_all_sessions_info(self) -> List[Dict]:
        """دریافت اطلاعات همه سشن‌ها"""
        return [self.get_session_info(key) for key in self.sessions.keys()]

    def print_status(self):
        """چاپ وضعیت فعلی سشن‌ها و همپوشانی‌ها"""
        current_time = self.get_current_time()
        print("\n" + "=" * 70)
        print(f"وضعیت سشن‌های معاملاتی - {current_time.strftime('%Y-%m-%d %H:%M:%S')}".center(70))
        print("=" * 70)

        # نمایش سشن‌های فعال
        print("\n📊 سشن‌های معاملاتی:")
        for session_info in self.get_all_sessions_info():
            status = "✓ فعال" if session_info['is_active'] else "✗ غیرفعال"
            print(f"  {session_info['name']:20} | {session_info['open']} - {session_info['close']} | {status}")

        # نمایش همپوشانی‌های فعال
        active_overlaps = self.get_active_overlaps()
        print("\n🔄 همپوشانی‌های فعال:")
        if active_overlaps:
            for overlap in active_overlaps:
                print(f"  {overlap['name']:30} | اولویت: {overlap['priority']}")
        else:
            print("  هیچ همپوشانی فعالی وجود ندارد")

        # وضعیت معامله
        should_trade, overlap_info = self.should_trade()
        print("\n💹 وضعیت معامله:")
        if should_trade:
            print(f"  ✓ زمان معامله است! (همپوشانی: {overlap_info['name']})")
        else:
            print("  ✗ زمان معامله نیست")

        print("=" * 70 + "\n")


# تست مستقل ماژول
if __name__ == "__main__":
    print("تست مدیریت سشن‌های معاملاتی")
    print("-" * 70)

    # ایجاد نمونه
    sm = SessionManager()

    # نمایش وضعیت فعلی
    sm.print_status()

    # تست زمان‌های مختلف
    print("\nتست زمان‌های مختلف:")
    print("-" * 70)

    test_times = [
        "04:30",  # توکیو
        "10:30",  # همپوشانی توکیو-لندن
        "15:30",  # همپوشانی لندن-نیویورک
        "22:00",  # نیویورک
        "02:00",  # خارج از سشن
    ]

    for time_str in test_times:
        hour, minute = map(int, time_str.split(':'))
        test_datetime = datetime.now(sm.timezone).replace(hour=hour, minute=minute)

        print(f"\n⏰ زمان تست: {time_str}")
        active_sessions = sm.get_active_sessions(test_datetime)
        print(f"   سشن‌های فعال: {', '.join(active_sessions) if active_sessions else 'هیچ'}")

        should_trade, overlap = sm.should_trade(test_datetime)
        if should_trade:
            print(f"   ✓ معامله: بله (همپوشانی: {overlap['name']})")
        else:
            print(f"   ✗ معامله: خیر")
