import threading
from flask import Flask, request, jsonify, render_template_string
import json
import telebot
from config import BOT_TOKEN, ADMIN_ID, ADMIN_KEY, DB_PATH
from database.db import init_db
from database import users as users_db
from database import games as games_db

# Import các module handler
from handlers import start, tao_ban, dat_cuoc, soc, nap_tien, rut_tien

# Khởi tạo Bot & Flask
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Đăng ký các handler cho bot
start.register_handlers(bot)
tao_ban.register_handlers(bot)
dat_cuoc.register_handlers(bot)
soc.register_handlers(bot)
nap_tien.register_handlers(bot)
rut_tien.register_handlers(bot)

# --- FLASK ROUTES ---
@app.route('/sepay-webhook', methods=['POST'])
def sepay_webhook():
    data = request.json
    if not data or data.get('transferType') != 'in': return jsonify({"success": True}), 200
    content = data.get('content', '')
    ma_don = next((word for word in content.split() if word.startswith('NAP')), None)
    if ma_don:
        gd = games_db.get_giao_dich_by_ma(ma_don)
        if gd and gd['trang_thai'] == 'cho':
            users_db.cong_diem(gd['user_id'], gd['so_diem'])
            games_db.cap_nhat_giao_dich(ma_don, 'done')
    return jsonify({"success": True}), 200

@app.route('/health', methods=['GET'])
def health(): return "OK", 200

@app.route('/user', methods=['GET'])
def get_user_json():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    uid = request.args.get('id')
    conn = games_db.get_conn() # Dùng tạm hàm get_conn từ games_db
    row = conn.execute('SELECT * FROM users WHERE user_id=?', (uid,)).fetchone()
    conn.close()
    if row: return jsonify(dict(row)), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/adduser', methods=['GET', 'POST'])
def add_user_html():
    if request.args.get('key') != ADMIN_KEY: return "403 Forbidden", 403
    msg = ""
    if request.method == 'POST':
        try:
            data = json.loads(request.form.get('user_json', ''))
            conn = games_db.get_conn()
            conn.execute('INSERT OR REPLACE INTO users (user_id, username, ho_ten, diem) VALUES (?,?,?,?)', 
                         (int(data['user_id']), data.get('username'), data.get('ho_ten'), data.get('diem', 0)))
            conn.commit(); conn.close()
            msg = f"✅ Đã cập nhật user {data['user_id']}!"
        except Exception as e: msg = f"❌ Lỗi: {e}"
    return f"<h2>Phục hồi User</h2><p>{msg}</p><form method='POST'><textarea name='user_json' style='width:100%;height:200px'></textarea><br><button type='submit'>Lưu</button></form>"

# --- CHẠY CHÍNH ---
if __name__ == '__main__':
    init_db()
    
    # Chạy Flask ngầm ở luồng riêng
    def run_flask():
        import os
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("🚀 Bot đang chạy bằng Telebot (Polling)...")
    bot.infinity_polling()
