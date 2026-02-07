from flask import Blueprint, request, jsonify, render_template_string, redirect, url_for, session
from functools import wraps
from database import db
from models import User, GameLog, Withdrawal, Referral, PromoCode, PromoCodeUsage, Task, TaskCompletion, Advertisement, AdView, Setting, AdminLog
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - لوحة التحكم</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
        .login-container{background:white;padding:40px;border-radius:20px;box-shadow:0 10px 30px rgba(0,0,0,0.3);width:90%;max-width:400px}
        h2{text-align:center;color:#667eea;margin-bottom:30px;font-size:28px}
        .form-group{margin-bottom:20px}
        label{display:block;margin-bottom:8px;color:#333;font-weight:bold;font-size:14px}
        input{width:100%;padding:12px;border:2px solid #ddd;border-radius:10px;font-size:16px;transition:border-color 0.3s}
        input:focus{border-color:#667eea;outline:none;box-shadow:0 0 0 3px rgba(102,126,234,0.1)}
        button{width:100%;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;transition:all 0.3s;box-shadow:0 4px 15px rgba(102,126,234,0.4)}
        button:hover{transform:scale(1.02);box-shadow:0 6px 20px rgba(102,126,234,0.6)}
        button:active{transform:scale(0.98)}
        .error{color:#dc3545;text-align:center;margin-top:10px;font-weight:bold;background:#f8d7da;padding:10px;border-radius:5px}
        .logo{font-size:48px;text-align:center;margin-bottom:20px;animation:spin 3s linear infinite}
        @keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🎰</div>
        <h2>🔐 تسجيل الدخول</h2>
        <form method="POST">
            <div class="form-group">
                <label>اسم المستخدم</label>
                <input type="text" name="username" required autofocus placeholder="أدخل اسم المستخدم">
            </div>
            <div class="form-group">
                <label>كلمة المرور</label>
                <input type="password" name="password" required placeholder="أدخل كلمة المرور">
            </div>
            <button type="submit">تسجيل الدخول</button>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </form>
    </div>
</body>
</html>
'''

@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == os.getenv('ADMIN_USERNAME', 'admin') and password == os.getenv('ADMIN_PASSWORD', 'admin123'):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template_string(ADMIN_LOGIN_TEMPLATE, error="بيانات تسجيل الدخول غير صحيحة")
    
    return render_template_string(ADMIN_LOGIN_TEMPLATE)

# ... (سأكمل باقي لوحة التحكم في الرد التالي بسبب الحد الأقصى للأحرف)