from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os
from datetime import datetime
import json
from instagram_service import InstagramService
from ai_service import AIService
from database_service import DatabaseService

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.urandom(24)
CORS(app)

# Initialize services
instagram_service = InstagramService()
ai_service = AIService()
db_service = DatabaseService()

@app.route('/')
def index():
    """صفحه اصلی رابط کاربری"""
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    """لاگین به اینستاگرام"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'یوزرنیم و پسورد الزامی است'}), 400

        # لاگین به اینستاگرام
        result = instagram_service.login(username, password)

        if result['success']:
            session['instagram_username'] = username
            session['logged_in'] = True
            return jsonify({'success': True, 'message': 'ورود موفقیت‌آمیز'})
        else:
            return jsonify({'error': result['error']}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """خروج از اینستاگرام"""
    session.clear()
    instagram_service.logout()
    return jsonify({'success': True, 'message': 'خروج موفقیت‌آمیز'})

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """دریافت لیست دایرکت‌ها"""
    try:
        if not session.get('logged_in'):
            return jsonify({'error': 'لطفاً ابتدا وارد شوید'}), 401

        messages = instagram_service.get_direct_messages()
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/<thread_id>', methods=['GET'])
def get_conversation(thread_id):
    """دریافت مکالمه کامل یک دایرکت"""
    try:
        if not session.get('logged_in'):
            return jsonify({'error': 'لطفاً ابتدا وارد شوید'}), 401

        conversation = instagram_service.get_conversation(thread_id)
        return jsonify({'success': True, 'conversation': conversation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-message', methods=['POST'])
def send_message():
    """ارسال پیام به یک کاربر"""
    try:
        if not session.get('logged_in'):
            return jsonify({'error': 'لطفاً ابتدا وارد شوید'}), 401

        data = request.json
        thread_id = data.get('thread_id')
        message = data.get('message')

        if not thread_id or not message:
            return jsonify({'error': 'thread_id و message الزامی است'}), 400

        result = instagram_service.send_message(thread_id, message)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/train-agent', methods=['POST'])
def train_agent():
    """آموزش ایجنت با اطلاعات جدید"""
    try:
        data = request.json
        training_type = data.get('type')  # 'text' or 'voice'
        content = data.get('content')

        if not content:
            return jsonify({'error': 'محتوای آموزشی الزامی است'}), 400

        # ذخیره اطلاعات آموزشی در دیتابیس
        db_service.save_training_data(training_type, content)

        return jsonify({'success': True, 'message': 'اطلاعات آموزشی ذخیره شد'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auto-reply', methods=['POST'])
def auto_reply():
    """پاسخ خودکار هوشمند به یک پیام"""
    try:
        if not session.get('logged_in'):
            return jsonify({'error': 'لطفاً ابتدا وارد شوید'}), 401

        data = request.json
        thread_id = data.get('thread_id')
        user_message = data.get('user_message')

        if not thread_id or not user_message:
            return jsonify({'error': 'thread_id و user_message الزامی است'}), 400

        # دریافت تاریخچه مکالمه
        conversation_history = instagram_service.get_conversation(thread_id)

        # دریافت اطلاعات آموزشی
        training_data = db_service.get_training_data()

        # دریافت تعداد پیام‌های قبلی این مکالمه
        conversation_count = db_service.get_conversation_count(thread_id)

        # تولید پاسخ هوشمند با AI
        ai_response = ai_service.generate_response(
            user_message=user_message,
            conversation_history=conversation_history,
            training_data=training_data,
            conversation_count=conversation_count
        )

        # ارسال پاسخ
        instagram_service.send_message(thread_id, ai_response['message'])

        # ذخیره در دیتابیس
        db_service.save_conversation(thread_id, user_message, ai_response['message'], conversation_count + 1)

        return jsonify({
            'success': True,
            'response': ai_response['message'],
            'should_close_sale': ai_response.get('should_close_sale', False),
            'conversation_stage': conversation_count + 1
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """تنظیمات ایجنت"""
    try:
        if request.method == 'GET':
            settings = db_service.get_settings()
            return jsonify({'success': True, 'settings': settings})
        else:
            data = request.json
            db_service.save_settings(data)
            return jsonify({'success': True, 'message': 'تنظیمات ذخیره شد'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def statistics():
    """آمار و گزارش‌ها"""
    try:
        stats = db_service.get_statistics()
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Instagram DM Agent در حال اجرا...")
    print("📱 برای دسترسی به رابط کاربری به آدرس http://localhost:5000 بروید")
    app.run(debug=True, host='0.0.0.0', port=5000)
