import threading
import os
import json
import re
import time
import requests
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

# ==============================================================================
# 1. CẤU HÌNH API THUEAPIBANK (TỰ ĐỘNG CÀO TIỀN)
# ==============================================================================
BANK_API = "https://thueapibank.vn/historyapitpbv2/6ca255a6218e69fd95feb4348844a220"
CHECK_BANK_SECONDS = 10
processed_txs = set()

def check_bank_api():
    print("🚀 Bắt đầu chạy luồng cào API Bank...")
    while True:
        try:
            response = requests.get(BANK_API, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') != 'success':
                    time.sleep(CHECK_BANK_SECONDS)
                    continue
                
                for tx in data.get('transactions', []):
                    tx_id = tx.get('transactionID')
                    amount = tx.get('amount', 0)
                    content = tx.get('description', '')
                    tx_type = tx.get('type', '')
                    
                    if tx_type == 'IN' and tx_id and tx_id not in processed_txs:
                        match = re.search(r'(NAP\d+)', content)
                        if match:
                            ma_don = match.group(1)
                            gd = games_db.get_giao_dich_by_ma(ma_don)
                            if gd and gd['trang_thai'] == 'cho':
                                games_db.cap_nhat_giao_dich(ma_don, 'done')
                                users_db.cong_diem(gd['user_id'], gd['so_diem'])
                                users_db.cong_tien_nap(gd['user_id'], gd['so_diem'])
                                print(f"🎉 Đã cộng {gd['so_diem']} điểm cho user {gd['user_id']}")
                                try:
                                    bot.send_message(gd['user_id'], f"🎉 <b>NẠP TIỀN THÀNH CÔNG</b>\nSố tiền: +{amount:,}đ\nĐiểm nhận: +{gd['so_diem']:,} điểm", parse_mode='HTML')
                                except: pass
                        processed_txs.add(tx_id)
        except Exception as e:
            print(f"Lỗi API Bank: {e}")
        time.sleep(CHECK_BANK_SECONDS)

# ==============================================================================
# 2. CÁC ENDPOINT FLASK (ADMIN / BACKUP)
# ==============================================================================
@app.route('/health', methods=['GET'])
def health(): return "OK", 200

@app.route('/user', methods=['GET'])
def get_user_json():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    uid = request.args.get('id')
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
            conn.execute('INSERT OR REPLACE INTO users (user_id, username, ho_ten, diem, tong_nap, da_cuoc) VALUES (?,?,?,?,?,?)', 
                         (int(data['user_id']), data.get('username'), data.get('ho_ten'), data.get('diem', 0), data.get('tong_nap', 0), data.get('da_cuoc', 0)))
            conn.commit(); conn.close()
            msg = f"✅ Đã cập nhật user <b>{data['user_id']}</b>!"
        except Exception as e: 
            msg = f"❌ Lỗi: {str(e)}"
    return f"<h2>Phục Hồi User</h2><p>{msg}</p><form method='POST'><textarea name='user_json' style='width:100%;height:200px'></textarea><br><button type='submit'>Lưu</button></form>"

# ==============================================================================
# 3. HÀM CHẠY CHÍNH
# ==============================================================================
if __name__ == '__main__':
    init_db()
    # Chạy Flask
    def run_flask():
        port = int(os.environ.get('PORT', 10000))
        app.run(host='0.0.0.0', port=port)
    threading.Thread(target=run_flask, daemon=True).start()
    # Chạy luồng cào Bank
    threading.Thread(target=check_bank_api, daemon=True).start()
    
    print("🚀 Bot Bầu Cua đang chạy...")
    bot.infinity_polling()
