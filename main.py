import threading
import os
import json
from flask import Flask, request, jsonify
import telebot
from config import BOT_TOKEN, ADMIN_ID, ADMIN_KEY, DB_PATH
from database.db import init_db, get_conn
from database import users as users_db
from database import games as games_db

# Import các module handler
from handlers import start, tao_ban, dat_cuoc, soc, nap_tien, rut_tien, admin

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Đăng ký handler
start.register_handlers(bot)
tao_ban.register_handlers(bot)
dat_cuoc.register_handlers(bot)
soc.register_handlers(bot)
nap_tien.register_handlers(bot)
rut_tien.register_handlers(bot)
admin.register_handlers(bot)

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
    username = request.args.get('username')
    if not uid and not username: return jsonify({"error": "Thiếu ?id hoặc ?username"}), 400

    conn = get_conn()
    if uid:
        row = conn.execute('SELECT * FROM users WHERE user_id=?', (uid,)).fetchone()
    else:
        row = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    conn.close()
    
    if row: 
        u_dict = dict(row); u_dict['user_id'] = str(u_dict['user_id'])
        return jsonify(u_dict), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/users', methods=['GET'])
def get_all_users_json():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    conn = get_conn()
    users = conn.execute('SELECT * FROM users ORDER BY diem DESC').fetchall()
    conn.close()
    data = []
    for u in users:
        u_dict = dict(u); u_dict['user_id'] = str(u_dict['user_id'])
        data.append(u_dict)
    return jsonify(data), 200

# --- ENDPOINT XEM TRƯỚC KẾT QUẢ ---
@app.route('/xem', methods=['GET'])
def xem_ket_qua_truoc():
    if request.args.get('key') != ADMIN_KEY: 
        return jsonify({"error": "403 Forbidden"}), 403
        
    conn = get_conn()
    # Tìm bàn đang chờ sóc
    ban = conn.execute("SELECT * FROM bans WHERE trang_thai='het_gio' ORDER BY ban_id DESC LIMIT 1").fetchone()
    conn.close()
    
    if ban and ban['ket_qua']:
        return jsonify({
            "ban_id": ban['ban_id'],
            "chat_id": ban['chat_id'],
            "cai_id": ban['cai_id'],
            "ket_qua_sap_ra": ban['ket_qua'].split(',')
        }), 200
        
    return jsonify({"message": "Không có bàn nào đang chờ Sóc."}), 200

@app.route('/adduser', methods=['GET', 'POST'])
def add_user_html():
    if request.args.get('key') != ADMIN_KEY: return "403 Forbidden", 403
    msg = ""
    if request.method == 'POST':
        try:
            raw_json = request.form.get('user_json', '').strip()
            data = json.loads(raw_json)
            if isinstance(data, list):
                if len(data) == 0: raise ValueError("Mảng JSON rỗng.")
                data = data[0]
            if 'user_id' not in data: raise ValueError("JSON thiếu 'user_id'")

            conn = get_conn()
            conn.execute('INSERT OR REPLACE INTO users (user_id, username, ho_ten, diem) VALUES (?,?,?,?)', 
                         (int(data['user_id']), data.get('username'), data.get('ho_ten'), data.get('diem', 0)))
            conn.commit(); conn.close()
            msg = f"✅ Đã cập nhật user <b>{data['user_id']}</b> với <b>{data.get('diem', 0)}</b> điểm!"
        except Exception as e: 
            msg = f"❌ Lỗi: {str(e)}"

    html = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin - Phục Hồi Dữ Liệu</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px; display: flex; justify-content: center; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }}
            h2 {{ color: #333; text-align: center; margin-bottom: 20px; }}
            .message {{ padding: 15px; margin-bottom: 20px; border-radius: 5px; font-weight: bold; text-align: center; }}
            .success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .error {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            textarea {{ width: 100%; height: 200px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-family: monospace; box-sizing: border-box; margin-bottom: 15px; resize: vertical; }}
            .btn-group {{ display: flex; gap: 10px; }}
            button {{ flex: 1; padding: 12px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; transition: 0.3s; }}
            button:hover {{ background: #218838; }}
            .btn-copy {{ background: #007bff; }}
            .btn-copy:hover {{ background: #0069d9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔄 Phục Hồi Dữ Liệu User</h2>
            {f'<div class="message {"success" if "✅" in msg else "error"}">{msg}</div>' if msg else ''}
            <form method="POST">
                <p style="color: #666; font-size: 14px;">Dán nội dung JSON (copy từ endpoint <code>/user</code> hoặc <code>/users</code>) vào ô bên dưới:</p>
                <textarea id="jsonInput" name="user_json" placeholder='Ví dụ: {{"user_id": "123456", "username": "abc", "ho_ten": "Nguyen Van A", "diem": 5000}}'></textarea>
                <div class="btn-group">
                    <button type="button" class="btn-copy" onclick="copyText()">📋 Dán Nhanh</button>
                    <button type="submit">💾 Lưu Vào Database</button>
                </div>
            </form>
        </div>
        <script>
            function copyText() {{
                navigator.clipboard.readText().then(text => {{
                    document.getElementById('jsonInput').value = text;
                }}).catch(err => {{
                    alert('Trình duyệt không hỗ trợ dán tự động. Vui lòng dán thủ công.');
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html

# --- CHẠY CHÍNH ---
if __name__ == '__main__':
    init_db()
    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Bot đang chạy...")
    bot.infinity_polling()
