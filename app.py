from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from database import db
from utils import TelegramAuth, GameLogic
from admin_dashboard import admin_bp
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-in-production')
CORS(app)

# Register admin blueprint
app.register_blueprint(admin_bp)

# ==================== MAIN WEBAPP ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>لعبة الحظ 🎰</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif}
        body{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding-bottom:80px}
        .container{max-width:500px;margin:0 auto;padding:20px}
        .header{background:white;border-radius:20px;padding:20px;margin-bottom:20px;box-shadow:0 4px 15px rgba(0,0,0,0.1);text-align:center}
        .user-info{display:flex;align-items:center;justify-content:center;gap:15px;margin-bottom:15px}
        .user-avatar{width:60px;height:60px;border-radius:50%;background:#f0f0f0;display:flex;align-items:center;justify-content:center;font-size:24px;color:#667eea}
        .user-name{font-size:18px;font-weight:bold;color:#333}
        .stats{display:flex;justify-content:space-around;margin-top:15px;padding:10px;background:#f8f9fa;border-radius:10px}
        .stat-item{text-align:center}
        .stat-value{font-size:20px;font-weight:bold;color:#667eea}
        .stat-label{font-size:12px;color:#666}
        .game-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:30px}
        .grid-item{aspect-ratio:1;background:rgba(255,255,255,0.9);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:bold;color:#333;box-shadow:0 2px 8px rgba(0,0,0,0.1);transition:all 0.3s ease}
        .grid-item.active{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;transform:scale(1.1);box-shadow:0 4px 20px rgba(102,126,234,0.5)}
        .play-button{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);width:90%;max-width:400px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;padding:20px;border-radius:50px;font-size:18px;font-weight:bold;cursor:pointer;box-shadow:0 6px 20px rgba(102,126,234,0.4);transition:all 0.3s ease}
        .play-button:hover{transform:translateX(-50%) scale(1.05);box-shadow:0 8px 25px rgba(102,126,234,0.6)}
        .play-button:disabled{background:#ccc;cursor:not-allowed;transform:translateX(-50%)}
        .result-modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);display:flex;align-items:center;justify-content:center;z-index:1000;opacity:0;pointer-events:none;transition:opacity 0.3s ease}
        .result-modal.show{opacity:1;pointer-events:all}
        .result-content{background:white;border-radius:20px;padding:30px;text-align:center;max-width:350px;width:90%;animation:modalSlideUp 0.5s ease}
        @keyframes modalSlideUp{from{transform:translateY(50px);opacity:0}to{transform:translateY(0);opacity:1}}
        .result-number{font-size:80px;font-weight:bold;margin:20px 0}
        .result-rare{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .result-normal{color:#667eea}
        .result-title{font-size:24px;font-weight:bold;margin-bottom:10px}
        .result-reward{font-size:18px;color:#666;margin:10px 0}
        .close-modal{background:#667eea;color:white;border:none;padding:12px 30px;border-radius:25px;font-size:16px;font-weight:bold;cursor:pointer;margin-top:20px;transition:all 0.3s ease}
        .close-modal:hover{background:#764ba2}
        .no-games{background:white;border-radius:20px;padding:30px;text-align:center;margin-bottom:20px}
        .invite-button{background:#667eea;color:white;border:none;padding:15px 30px;border-radius:25px;font-size:16px;font-weight:bold;cursor:pointer;margin-top:20px;width:100%}
        .nav{position:fixed;bottom:0;left:0;right:0;background:white;padding:10px;display:flex;justify-content:space-around;box-shadow:0 -2px 10px rgba(0,0,0,0.1)}
        .nav-item{display:flex;flex-direction:column;align-items:center;gap:4px;color:#999;font-size:12px;cursor:pointer}
        .nav-item.active{color:#667eea;font-weight:bold}
        .nav-icon{font-size:20px}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="user-info">
                <div class="user-avatar" id="userAvatar">👤</div>
                <div>
                    <div class="user-name" id="userName">جاري التحميل...</div>
                    <div id="userUsername" style="color:#666;font-size:14px">@username</div>
                </div>
            </div>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="gamesAvailable">0</div>
                    <div class="stat-label">ألعاب</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="balance">0</div>
                    <div class="stat-label">رصيد</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="rareWins">0</div>
                    <div class="stat-label">نادر</div>
                </div>
            </div>
        </div>
        
        <div class="game-grid" id="gameGrid"></div>
        
        <div class="no-games" id="noGamesMessage" style="display:none">
            <h3>🎮 لا توجد ألعاب متاحة!</h3>
            <p style="margin:15px 0;color:#666">ادعُ 3 أصدقاء للحصول على لعبة مجانية</p>
            <button class="invite-button" onclick="shareReferral()">دعوة الأصدقاء</button>
        </div>
    </div>
    
    <button class="play-button" id="playButton" onclick="startGame()">ابدأ اللعب 🎰</button>
    
    <div class="result-modal" id="resultModal">
        <div class="result-content">
            <div class="result-title" id="resultTitle">تهانينا!</div>
            <div class="result-number" id="resultNumber"></div>
            <div class="result-reward" id="resultReward"></div>
            <button class="close-modal" onclick="closeModal()">حسناً</button>
        </div>
    </div>

    <div class="nav">
        <div class="nav-item active" onclick="showSection('game')">
            <div class="nav-icon">🎮</div>
            <div>اللعبة</div>
        </div>
        <div class="nav-item" onclick="showSection('withdraw')">
            <div class="nav-icon">💳</div>
            <div>السحب</div>
        </div>
        <div class="nav-item" onclick="showSection('promo')">
            <div class="nav-icon">🎁</div>
            <div>رمز ترويجي</div>
        </div>
        <div class="nav-item" onclick="showSection('referral')">
            <div class="nav-icon">👥</div>
            <div>الإحالات</div>
        </div>
        <div class="nav-item" onclick="showSection('leaderboard')">
            <div class="nav-icon">🏆</div>
            <div>المتصدرين</div>
        </div>
    </div>

    <script>
        let tg = window.Telegram?.WebApp;
        let userData = tg?.initDataUnsafe?.user || {};
        let gameData = null;
        let isPlaying = false;
        
        if (tg) {
            tg.ready();
            tg.expand();
            loadGameData();
        }
        
        function loadGameData() {
            fetch('/api/user/data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({init_data:.initData})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    gameData = data.data;
                    updateUI();
                } else {
                    alert('خطأ في تحميل البيانات');
                }
            });
        }
        
        function updateUI() {
            document.getElementById('userName').textContent = userData.first_name || 'مستخدم';
            document.getElementById('userUsername').textContent = userData.username ? '@' + userData.username : '';
            document.getElementById('gamesAvailable').textContent = gameData.games_available;
            document.getElementById('balance').textContent = gameData.balance.toFixed(2);
            document.getElementById('rareWins').textContent = gameData.rare_wins;
            
            const btn = document.getElementById('playButton');
            if (gameData.games_available <= 0) {
                btn.disabled = true;
                document.getElementById('noGamesMessage').style.display = 'block';
            } else {
                btn.disabled = false;
                document.getElementById('noGamesMessage').style.display = 'none';
            }
            
            generateGrid();
        }
        
        function generateGrid() {
            const grid = document.getElementById('gameGrid');
            grid.innerHTML = '';
            for (let i = 0; i < 25; i++) {
                const num = Math.floor(Math.random() * 20) + 1;
                const item = document.createElement('div');
                item.className = 'grid-item';
                item.textContent = num;
                grid.appendChild(item);
            }
        }
        
        function startGame() {
            if (isPlaying || gameData.games_available <= 0) return;
            isPlaying = true;
            const btn = document.getElementById('playButton');
            btn.disabled = true;
            btn.textContent = 'جاري اللعب...';
            
            const items = document.querySelectorAll('.grid-item');
            let idx = 0;
            const total = 30;
            
            const int = setInterval(() => {
                items.forEach(i => i.classList.remove('active'));
                items[Math.floor(Math.random() * items.length)].classList.add('active');
                idx++;
                if (idx >= total) {
                    clearInterval(int);
                    fetch('/api/game/play', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({init_data: tg.initData})
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            showResult(data.data);
                            gameData = data.data.user;
                            updateUI();
                        } else {
                            alert(data.message || 'خطأ');
                            btn.disabled = false;
                            btn.textContent = 'ابدأ اللعب 🎰';
                        }
                        isPlaying = false;
                    })
                    .catch(e => {
                        alert('خطأ في الاتصال');
                        btn.disabled = false;
                        btn.textContent = 'ابدأ اللعب 🎰';
                        isPlaying = false;
                    });
                }
            }, 100);
        }
        
        function showResult(r) {
            const m = document.getElementById('resultModal');
            const num = document.getElementById('resultNumber');
            const title = document.getElementById('resultTitle');
            const reward = document.getElementById('resultReward');
            
            num.textContent = r.number;
            reward.textContent = r.reward > 0 ? `+${r.reward.toFixed(2)} ج` : '';
            
            if (r.win_type === 'rare') {
                num.className = 'result-number result-rare';
                title.textContent = '🎉 فوز نادر!';
            } else {
                num.className = 'result-number result-normal';
                title.textContent = '🎊 فوز!';
            }
            
            m.classList.add('show');
        }
        
        function closeModal() {
            document.getElementById('resultModal').classList.remove('show');
        }
        
        function shareReferral() {
            const link = `https://t.me/${tg.initDataUnsafe.bot_username}?start=${gameData.referral_code}`;
            tg.shareText(`🎮 تعال العب معي لعبة الحظ!\\n🎯 الرابط: ${link}\\n\\nاربح جوائز رائعة!`);
        }
        
        function showSection(section) {
            alert('سيتم إضافة الأقسام قريباً!');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/user/data', methods=['POST'])
def get_user_data():
    try:
        data = request.json
        init_data = data.get('init_data', '')
        bot_token = os.getenv('BOT_TOKEN', '')
        
        if not TelegramAuth.validate_init_data(init_data, bot_token):
            return jsonify({'success': False, 'message': 'Invalid authentication'}), 401
        
        user_data = TelegramAuth.parse_user_data(init_data)
        telegram_id = user_data.get('id')
        
        if not telegram_id:
            return jsonify({'success': False, 'message': 'Invalid user data'}), 400
        
        # Get referral code if exists
        start_param = data.get('start_param', '')
        referred_by_code = None
        
        # Create or get user
        user_info = db.create_user(
            telegram_id=telegram_id,
            username=user_data.get('username'),
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            photo_url=user_data.get('photo_url'),
            referred_by=referred_by_code
        )
        
        return jsonify({
            'success': True,
            'data': user_info
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/game/play', methods=['POST'])
def play_game():
    try:
        data = request.json
        init_data = data.get('init_data', '')
        bot_token = os.getenv('BOT_TOKEN', '')
        
        if not TelegramAuth.validate_init_data(init_data, bot_token):
            return jsonify({'success': False, 'message': 'Invalid authentication'}), 401
        
        user_data = TelegramAuth.parse_user_data(init_data)
        telegram_id = user_data.get('id')
        
        if not telegram_id:
            return jsonify({'success': False, 'message': 'Invalid user data'}), 400
        
        # Check if user has games
        if not db.use_game(telegram_id):
            return jsonify({'success': False, 'message': 'No games available'}), 400
        
        # Generate result
        rare_chance = float(os.getenv('RARE_WIN_CHANCE', 0.10))
        result = GameLogic.generate_result(rare_chance)
        
        # Record game
        db.record_game(
            user_id=telegram_id,
            result_number=result['number'],
            win_type=result['win_type'],
            reward=result['reward']
        )
        
        # Get updated user data
        user_info = db.get_user(telegram_id)
        
        return jsonify({
            'success': True,
            'data': {
                'number': result['number'],
                'win_type': result['win_type'],
                'reward': result['reward'],
                'user': user_info
            }
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)