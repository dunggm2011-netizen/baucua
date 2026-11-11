import threading
import os
import json
import re
from flask import Flask, request, jsonify
import telebot
from config import BOT_TOKEN, ADMIN_ID, ADMIN_KEY, DB_PATH, TEN_CON_VAT
from database.db import init_db, get_conn
from database import users as users_db
from database import games as games_db

from handlers import start, tao_ban, dat_cuoc, soc, nap_tien, rut_tien, admin

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

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
    API_KEY_SEPAY = "DMAS9CFVPYR8ZHSLGU6UBRJOKWKQXB2TCIBL00WYFI3LRODNNC2HJEJRFSGKA1PO"
    
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.replace('Apikey ', '').strip()
            if token != API_KEY_SEPAY:
                print("❌ Lỗi: API Key không khớp!")
                return jsonify({"error": "Unauthorized"}), 401
                
        data = request.json
        if not data or data.get('transferType') != 'in': 
            return jsonify({"success": True}), 200
            
        content = data.get('content', '')
        print(f"📥 Nhận Webhook. Nội dung: {content}")
        
        match = re.search(r'(NAP\d+)', content)
        if match:
            ma_don = match.group(1)
            print(f"🔍 Mã đơn tìm được: {ma_don}")
            
            gd = games_db.get_giao_dich_by_ma(ma_don)
            
            if gd and gd['trang_thai'] == 'cho':
                games_db.cap_nhat_giao_dich(ma_don, 'done')
                users_db.cong_diem(gd['user_id'], gd['so_diem'])
                users_db.cong_tien_nap(gd['user_id'], gd['so_diem']) 
                print(f"🎉 THÀNH CÔNG: Đã cộng {gd['so_diem']} điểm cho user {gd['user_id']}")
                
                try:
                    u_info = users_db.get_user(gd['user_id'])
                    ho_ten = u_info['ho_ten'] if u_info else "Người chơi"
                    so_du_moi = users_db.get_diem(gd['user_id'])
                    
                    text = (
                        f"🎉 <b>NẠP TIỀN THÀNH CÔNG</b> 🎉\n"
                        f"-------------\n"
                        f"👤 Người nạp: <b>{ho_ten}</b>\n"
                        f"💰 Số tiền: <code>+{gd['so_tien']:,} đ</code>\n"
                        f"🎁 Điểm nhận: <code>+{gd['so_diem']:,} điểm</code>\n"
                        f"🧾 Nội dung CK: <code>{ma_don}</code>\n"
                        f"-------------\n"
                        f"💵 Số dư hiện tại: <b>{so_du_moi:,} điểm</b>"
                    )
                    bot.send_message(gd['user_id'], text, parse_mode='HTML')
                except Exception as e:
                    print(f"Lỗi gửi tin nhắn: {e}")
            else:
                print("⚠️ Không tìm thấy đơn trong Database.")
                    
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"❌ LỖI WEBHOOK: {str(e)}")
        return jsonify({"success": True}), 200

@app.route('/health', methods=['GET'])
def health(): return "OK", 200

@app.route('/user', methods=['GET'])
def get_user_json():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    uid = request.args.get('id')
    if not uid: return jsonify({"error": "Thiếu ?id"}), 400
    conn = get_conn()
    row = conn.execute('SELECT * FROM users WHERE user_id=%s', (uid,)).fetchone()
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
        ket_qua_ma = ban['ket_qua'].split(',')
        ket_qua_chu = [TEN_CON_VAT[c] for c in ket_qua_ma]
        return jsonify({"ban_id": ban['ban_id'], "ket_qua_sap_ra": ket_qua_chu}), 200
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
            # Sửa câu lệnh SQL cho Postgres (%s thay vì ?)
            conn.execute('''INSERT INTO users (user_id, username, ho_ten, diem, tong_nap, da_cuoc) 
                            VALUES (%s, %s, %s, %s, %s, %s) 
                            ON CONFLICT (user_id) DO UPDATE 
                            SET diem=EXCLUDED.diem, tong_nap=EXCLUDED.tong_nap, da_cuoc=EXCLUDED.da_cuoc''', 
                         (int(data['user_id']), data.get('username'), data.get('ho_ten'), data.get('diem', 0), data.get('tong_nap', 0), data.get('da_cuoc', 0)))
            conn.commit(); conn.close()
            msg = f"✅ Đã cập nhật user <b>{data['user_id']}</b>!"
        except Exception as e: 
            msg = f"❌ Lỗi: {str(e)}"
    return f"<h2>Phục Hồi User</h2><p>{msg}</p><form method='POST'><textarea name='user_json' style='width:100%;height:200px'></textarea><br><button type='submit' style='padding:10px 20px;margin-top:10px;'>Lưu</button></form>"

if __name__ == '__main__':
    init_db()
    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Bot đang chạy...")
    bot.infinity_polling()
