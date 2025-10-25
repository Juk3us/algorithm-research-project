import sqlite3
import json
from datetime import datetime
import os

class DatabaseService:
    """سرویس مدیریت دیتابیس"""

    def __init__(self, db_path='../database/instagram_agent.db'):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """ایجاد جداول دیتابیس"""
        # ایجاد پوشه database اگر وجود ندارد
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # جدول اطلاعات آموزشی
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول مکالمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                stage INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # جدول تنظیمات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # تنظیمات پیش‌فرض
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES
            ('auto_reply_enabled', 'false'),
            ('max_conversation_stages', '5'),
            ('response_delay_seconds', '3')
        ''')

        conn.commit()
        conn.close()

    def save_training_data(self, training_type, content):
        """ذخیره اطلاعات آموزشی"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO training_data (type, content) VALUES (?, ?)',
            (training_type, content)
        )

        conn.commit()
        conn.close()

        print(f"✅ اطلاعات آموزشی ذخیره شد: {content[:50]}...")

    def get_training_data(self):
        """دریافت تمام اطلاعات آموزشی"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT type, content, created_at FROM training_data ORDER BY created_at DESC')
        rows = cursor.fetchall()

        conn.close()

        return [
            {
                'type': row[0],
                'content': row[1],
                'created_at': row[2]
            }
            for row in rows
        ]

    def save_conversation(self, thread_id, user_message, bot_response, stage):
        """ذخیره یک مکالمه"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'INSERT INTO conversations (thread_id, user_message, bot_response, stage) VALUES (?, ?, ?, ?)',
            (thread_id, user_message, bot_response, stage)
        )

        conn.commit()
        conn.close()

    def get_conversation_count(self, thread_id):
        """دریافت تعداد پیام‌های یک مکالمه"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM conversations WHERE thread_id = ?', (thread_id,))
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_conversation_history(self, thread_id):
        """دریافت تاریخچه مکالمه یک thread"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'SELECT user_message, bot_response, stage, created_at FROM conversations WHERE thread_id = ? ORDER BY created_at ASC',
            (thread_id,)
        )
        rows = cursor.fetchall()

        conn.close()

        return [
            {
                'user_message': row[0],
                'bot_response': row[1],
                'stage': row[2],
                'created_at': row[3]
            }
            for row in rows
        ]

    def save_settings(self, settings_dict):
        """ذخیره تنظیمات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for key, value in settings_dict.items():
            cursor.execute(
                'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)',
                (key, str(value), datetime.now())
            )

        conn.commit()
        conn.close()

    def get_settings(self):
        """دریافت تنظیمات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT key, value FROM settings')
        rows = cursor.fetchall()

        conn.close()

        return {row[0]: row[1] for row in rows}

    def get_statistics(self):
        """آمار و گزارش‌ها"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # تعداد کل مکالمات
        cursor.execute('SELECT COUNT(DISTINCT thread_id) FROM conversations')
        total_conversations = cursor.fetchone()[0]

        # تعداد کل پیام‌ها
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_messages = cursor.fetchone()[0]

        # تعداد مکالمات در هر مرحله
        cursor.execute('SELECT stage, COUNT(*) FROM conversations GROUP BY stage')
        stage_stats = dict(cursor.fetchall())

        # تعداد مکالمات امروز
        cursor.execute('SELECT COUNT(DISTINCT thread_id) FROM conversations WHERE DATE(created_at) = DATE("now")')
        today_conversations = cursor.fetchone()[0]

        conn.close()

        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'stage_distribution': stage_stats,
            'today_conversations': today_conversations
        }

    def delete_training_data(self, training_id):
        """حذف یک آیتم آموزشی"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM training_data WHERE id = ?', (training_id,))

        conn.commit()
        conn.close()

    def clear_all_conversations(self):
        """پاک کردن تمام مکالمات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM conversations')

        conn.commit()
        conn.close()
