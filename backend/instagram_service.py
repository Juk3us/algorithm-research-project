from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes, ChallengeRequired
import json
import os
from datetime import datetime

class InstagramService:
    """سرویس مدیریت ارتباط با اینستاگرام"""

    def __init__(self):
        self.client = None
        self.username = None
        self.session_file = 'instagram_session.json'

    def login(self, username, password):
        """ورود به اینستاگرام"""
        try:
            self.client = Client()
            self.username = username

            # تلاش برای بارگذاری session قبلی
            if os.path.exists(self.session_file):
                try:
                    self.client.load_settings(self.session_file)
                    self.client.login(username, password)
                    print(f"✅ ورود با session ذخیره شده موفق بود")
                    return {'success': True}
                except:
                    print("⚠️ Session قبلی معتبر نیست، ورود جدید...")

            # ورود جدید
            self.client.login(username, password)

            # ذخیره session برای استفاده‌های بعدی
            self.client.dump_settings(self.session_file)

            print(f"✅ ورود به اکانت {username} موفق بود")
            return {'success': True}

        except LoginRequired as e:
            return {'success': False, 'error': 'یوزرنیم یا پسورد اشتباه است'}
        except ChallengeRequired as e:
            return {'success': False, 'error': 'اینستاگرام نیاز به تایید هویت دارد. لطفاً از اپلیکیشن موبایل وارد شوید'}
        except PleaseWaitFewMinutes as e:
            return {'success': False, 'error': 'لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید'}
        except Exception as e:
            return {'success': False, 'error': f'خطا در ورود: {str(e)}'}

    def logout(self):
        """خروج از اینستاگرام"""
        if self.client:
            self.client = None
        if os.path.exists(self.session_file):
            os.remove(self.session_file)

    def get_direct_messages(self, limit=20):
        """دریافت لیست دایرکت‌ها"""
        if not self.client:
            raise Exception("لطفاً ابتدا وارد شوید")

        try:
            threads = self.client.direct_threads(amount=limit)

            messages_list = []
            for thread in threads:
                last_message = thread.messages[0] if thread.messages else None

                messages_list.append({
                    'thread_id': thread.id,
                    'users': [{'username': user.username, 'full_name': user.full_name} for user in thread.users],
                    'last_message': {
                        'text': last_message.text if last_message else '',
                        'timestamp': last_message.timestamp.isoformat() if last_message else ''
                    } if last_message else None,
                    'unread_count': thread.unread_count if hasattr(thread, 'unread_count') else 0
                })

            return messages_list
        except Exception as e:
            raise Exception(f"خطا در دریافت دایرکت‌ها: {str(e)}")

    def get_conversation(self, thread_id, limit=50):
        """دریافت مکالمه کامل یک دایرکت"""
        if not self.client:
            raise Exception("لطفاً ابتدا وارد شوید")

        try:
            thread = self.client.direct_thread(thread_id, amount=limit)

            messages = []
            for msg in thread.messages:
                messages.append({
                    'id': msg.id,
                    'text': msg.text or '',
                    'user_id': str(msg.user_id),
                    'timestamp': msg.timestamp.isoformat(),
                    'is_sent_by_me': str(msg.user_id) == str(self.client.user_id)
                })

            # مرتب‌سازی از قدیمی به جدید
            messages.reverse()

            return {
                'thread_id': thread_id,
                'messages': messages,
                'users': [{'username': user.username, 'full_name': user.full_name} for user in thread.users]
            }
        except Exception as e:
            raise Exception(f"خطا در دریافت مکالمه: {str(e)}")

    def send_message(self, thread_id, message_text):
        """ارسال پیام به یک thread"""
        if not self.client:
            raise Exception("لطفاً ابتدا وارد شوید")

        try:
            # ارسال پیام
            result = self.client.direct_send(message_text, thread_ids=[thread_id])

            print(f"✅ پیام ارسال شد: {message_text[:50]}...")
            return {'success': True, 'message_id': result}
        except Exception as e:
            raise Exception(f"خطا در ارسال پیام: {str(e)}")

    def send_message_to_user(self, username, message_text):
        """ارسال پیام به یک کاربر خاص"""
        if not self.client:
            raise Exception("لطفاً ابتدا وارد شوید")

        try:
            user_id = self.client.user_id_from_username(username)
            result = self.client.direct_send(message_text, user_ids=[user_id])

            print(f"✅ پیام به {username} ارسال شد")
            return {'success': True, 'message_id': result}
        except Exception as e:
            raise Exception(f"خطا در ارسال پیام: {str(e)}")
