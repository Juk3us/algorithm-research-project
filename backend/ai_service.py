import os
from anthropic import Anthropic
import json

class AIService:
    """سرویس هوش مصنوعی برای تولید پاسخ‌های هوشمند"""

    def __init__(self):
        # می‌توانید از Claude API یا OpenAI استفاده کنید
        # برای استفاده از Claude:
        self.api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.client = None
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)

    def generate_response(self, user_message, conversation_history, training_data, conversation_count):
        """
        تولید پاسخ هوشمند بر اساس:
        - پیام کاربر
        - تاریخچه مکالمه
        - اطلاعات آموزشی
        - تعداد مرحله مکالمه (برای فروش 5 مرحله‌ای)
        """

        # اگر API key تنظیم نشده، از پاسخ‌های از پیش تعریف شده استفاده کن
        if not self.client:
            return self._generate_fallback_response(user_message, conversation_count)

        # ساخت prompt برای AI
        system_prompt = self._build_system_prompt(training_data, conversation_count)
        conversation_context = self._build_conversation_context(conversation_history)

        try:
            # فراخوانی Claude API
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"{conversation_context}\n\nپیام جدید کاربر: {user_message}\n\nلطفاً یک پاسخ مناسب تولید کن."
                    }
                ]
            )

            response_text = message.content[0].text

            # تشخیص اینکه آیا زمان بستن فروش است یا نه
            should_close_sale = conversation_count >= 4

            return {
                'message': response_text,
                'should_close_sale': should_close_sale,
                'conversation_stage': conversation_count + 1
            }

        except Exception as e:
            print(f"خطا در فراخوانی AI: {str(e)}")
            return self._generate_fallback_response(user_message, conversation_count)

    def _build_system_prompt(self, training_data, conversation_count):
        """ساخت prompt سیستمی برای AI"""

        stages = {
            0: "مرحله 1: آشنایی و جلب توجه - با گرمی سلام کن و کنجکاوی مشتری را برانگیز",
            1: "مرحله 2: شناسایی نیاز - سوالات هوشمندانه بپرس تا نیاز مشتری را بفهمی",
            2: "مرحله 3: ارائه راه‌حل - محصول را به عنوان راه‌حل نیاز مشتری معرفی کن",
            3: "مرحله 4: رفع اعتراضات - به سوالات و نگرانی‌های مشتری پاسخ بده",
            4: "مرحله 5: بستن فروش - پیشنهاد نهایی و دعوت به خرید"
        }

        current_stage = stages.get(conversation_count, stages[4])

        training_context = "\n".join([f"- {item['content']}" for item in training_data]) if training_data else "اطلاعات آموزشی خاصی وجود ندارد"

        prompt = f"""شما یک فروشنده حرفه‌ای و هوشمند هستید که از طریق دایرکت اینستاگرام با مشتریان صحبت می‌کنید.

هدف شما: فروش محصول در حداکثر 5 مرحله گفتگو

مرحله فعلی: {current_stage}

اطلاعات محصول و آموزش‌های شما:
{training_context}

قوانین:
1. پاسخ‌های کوتاه و جذاب بنویسید (حداکثر 2-3 جمله)
2. از زبان فارسی روان و دوستانه استفاده کنید
3. در هر مرحله یک هدف مشخص داشته باشید
4. سوالاتی بپرسید که مشتری را درگیر کند
5. از اموجی استفاده کنید تا پیام‌ها دوستانه‌تر باشند
6. در مرحله 5، حتماً پیشنهاد خرید یا لینک پرداخت بدهید
7. هیچ‌وقت زیاد‌روی نکنید یا مزاحم نشوید

پاسخ شما باید مستقیم و بدون توضیحات اضافی باشد - فقط متن پیامی که باید ارسال شود."""

        return prompt

    def _build_conversation_context(self, conversation_history):
        """ساخت متن تاریخچه مکالمه"""
        if not conversation_history or not conversation_history.get('messages'):
            return "این اولین پیام در این مکالمه است."

        messages = conversation_history['messages'][-10:]  # فقط 10 پیام آخر

        context = "تاریخچه مکالمه:\n"
        for msg in messages:
            sender = "شما" if msg['is_sent_by_me'] else "مشتری"
            context += f"{sender}: {msg['text']}\n"

        return context

    def _generate_fallback_response(self, user_message, conversation_count):
        """پاسخ‌های پیش‌فرض زمانی که AI در دسترس نیست"""

        responses = {
            0: "سلام! 👋 خوشحالم که پیام دادی. چطور می‌تونم کمکت کنم؟",
            1: "ممنون از پیامت! 😊 دقیقاً به دنبال چی هستی؟ بگو تا بهترین پیشنهاد رو بهت بدم",
            2: "عالیه! 🎉 محصول ما دقیقاً برای نیاز تو طراحی شده. می‌خوای بیشتر بدونی؟",
            3: "سوال خوبیه! ✨ این محصول واقعاً ارزشش رو داره چون... نظرت چیه؟",
            4: "پیشنهاد ویژه برای تو: الان سفارش بده و تخفیف بگیر! 🎁 آماده‌ای؟"
        }

        return {
            'message': responses.get(conversation_count, responses[4]),
            'should_close_sale': conversation_count >= 4,
            'conversation_stage': conversation_count + 1
        }

    def transcribe_voice(self, audio_file_path):
        """تبدیل صدا به متن (برای آموزش با فایل صوتی)"""
        # اینجا می‌توانید از Whisper API یا سرویس‌های دیگر استفاده کنید
        try:
            # مثال با OpenAI Whisper (نیاز به نصب openai و تنظیم API key)
            # from openai import OpenAI
            # client = OpenAI()
            # with open(audio_file_path, "rb") as audio_file:
            #     transcript = client.audio.transcriptions.create(
            #         model="whisper-1",
            #         file=audio_file
            #     )
            # return transcript.text

            return "قابلیت تبدیل صدا به متن هنوز پیاده‌سازی نشده است"
        except Exception as e:
            raise Exception(f"خطا در تبدیل صدا به متن: {str(e)}")
