import threading
import os
import json
import hmac
import hashlib
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
    # Cấu hình Secret Key (HMAC-SHA256)
    SECRET_KEY = "DMAS9CFVPYR8ZHSLGU6UBRJOKWKQXB2TCIBL00WYFI3LRODNNC2HJEJRFSGKA1PO"
    
    print("\n" + "="*40)
    print("📥 NHẬN ĐƯỢC TÍN HIỆU TỪ SEPAY")
    
    try:
        # 1. Xác thực chữ ký HMAC (nếu SePay gửi)
        signature = request.headers.get('x-sepay-signature')
        if signature:
            expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), request.data, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                print("❌ Lỗi: Chữ ký HMAC không khớp!")
                return jsonify({"error": "Chữ ký không hợp lệ"}), 401
            print("✅ Xác thực HMAC thành công.")
        else:
            print("⚠️ Không có header x-sepay-signature (Bỏ qua xác thực).")
            
        # 2. Đọc dữ liệu
        data = request.json
        print(f"📦 Dữ liệu nhận được: {data}")
        
        if not data or data.get('transferType') != 'in': 
            print("⚠️ Bỏ qua: Không phải giao dịch tiền vào.")
            return jsonify({"success": True}), 200
            
        content = data.get('content', '')
        print(f"📝 Nội dung CK: '{content}'")
        
        # 3. Tìm mã đơn NAP...
        ma_don = next((word for word in content.split() if word.startswith('NAP')), None)
        print(f"🔍 Mã đơn tìm được: {ma_don}")
        
        if ma_don:
            gd = games_db.get_giao_dich_by_ma(ma_don)
            print(f"🗄️ Dữ liệu đơn trong DB: {gd}")
            
            if gd and gd['trang_thai'] == 'cho':
                users_db.cong_diem(gd['user_id'], gd['so_diem'])
                games_db.cap_nhat_giao_dich(ma_don, 'done')
                print(f"🎉 THÀNH CÔNG: Đã cộng {gd['so_diem']} điểm cho user {gd['user_id']}")
            else:
                print("⚠️ Không tìm thấy đơn trong Database (Có thể DB đã bị reset khi deploy, hoặc đơn đã được cộng rồi).")
        else:
            print("⚠️ Không tìm thấy từ khóa 'NAP' trong nội dung chuyển khoản.")
            
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"❌ LỖI WEBHOOK: {str(e)}")
        return jsonify({"success": True}), 200 # Luôn trả 200 để SePay không spam

@app.route('/health', methods=['GET'])
def health(): return "OK", 200

@app.route('/user', methods=['GET'])
def get_user_json():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    uid = request.args.get('id')
    if not uid: return jsonify({"error": "Thiếu ?id"}), 400

    conn = get_conn()
    row = conn.execute('SELECT * FROM users WHERE user_id=?', (uid,)).fetchone()
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

@app.route('/xem', methods=['GET'])
def xem_ket_qua_truoc():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    conn = get_conn()
    ban = conn.execute("SELECT * FROM bans WHERE trang_thai='het_gio' ORDER BY ban_id DESC LIMIT 1").fetchone()
    conn.close()
    if ban and ban['ket_qua']:
        return jsonify({"ban_id": ban['ban_id'], "ket_qua_sap_ra": ban['ket_qua'].split(',')}), 200
    return jsonify({"message": "Không có bàn nào đang chờ Sóc."}), 200

@app.route('/adduser', methods=['GET', 'POST'])
def add_user_html():
    if request.args.get('key') != ADMIN_KEY: return "403 Forbidden", 403
    msg = ""
    if request.method == 'POST':
        try:
            data = json.loads(request.form.get('user_json', '').strip())
            if isinstance(data, list):
                if len(data) == 0: raise ValueError("Mảng JSON rỗng.")
                data = data[0]
            conn = get_conn()
            conn.execute('INSERT OR REPLACE INTO users (user_id, username, ho_ten, diem) VALUES (?,?,?,?)', 
                         (int(data['user_id']), data.get('username'), data.get('ho_ten'), data.get('diem', 0)))
            conn.commit(); conn.close()
            msg = f"✅ Đã cập nhật user <b>{data['user_id']}</b>!"
        except Exception as e: 
            msg = f"❌ Lỗi: {str(e)}"
    return f"<h2>Phục Hồi User</h2><p>{msg}</p><form method='POST'><textarea name='user_json' style='width:100%;height:200px'></textarea><br><button type='submit' style='padding:10px 20px;margin-top:10px;'>Lưu</button></form>"

# --- CHẠY CHÍNH ---
if __name__ == '__main__':
    init_db()
    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Bot đang chạy...")
    bot.infinity_polling()
