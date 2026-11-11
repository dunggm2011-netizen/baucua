import threading, os, re, time, requests, sqlite3, random, json
from flask import Flask, request, jsonify
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import *

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ==============================================================================
# PHẦN 1: DATABASE
# ==============================================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, ho_ten TEXT, diem INTEGER DEFAULT 0, tong_nap INTEGER DEFAULT 0, da_cuoc INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS giao_dich (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, so_tien INTEGER, so_diem INTEGER, ma_don TEXT UNIQUE, trang_thai TEXT DEFAULT 'cho')''')
    c.execute('''CREATE TABLE IF NOT EXISTS bans (ban_id INTEGER PRIMARY KEY AUTOINCREMENT, cai_id INTEGER, chat_id INTEGER, trang_thai TEXT DEFAULT 'dang_cho', ket_qua TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cuoc (id INTEGER PRIMARY KEY AUTOINCREMENT, ban_id INTEGER, user_id INTEGER, cua TEXT, so_diem INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS yeu_cau_rut (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, so_diem INTEGER, stk TEXT, ten_chu_the TEXT, trang_thai TEXT DEFAULT 'cho_duyet')''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_conn(); row = conn.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone(); conn.close(); return row
def create_user(user_id, username, ho_ten):
    conn = get_conn(); conn.execute('INSERT OR IGNORE INTO users (user_id, username, ho_ten) VALUES (?,?,?)', (user_id, username, ho_ten)); conn.commit(); conn.close()
def get_diem(user_id):
    row = get_user(user_id); return row['diem'] if row else 0
def cong_diem(user_id, so_diem):
    conn = get_conn(); conn.execute('UPDATE users SET diem = diem + ? WHERE user_id=?', (so_diem, user_id)); conn.commit(); conn.close()
def tru_diem(user_id, so_diem):
    conn = get_conn(); row = conn.execute('SELECT diem FROM users WHERE user_id=?', (user_id,)).fetchone()
    if not row or row['diem'] < so_diem: conn.close(); return False
    conn.execute('UPDATE users SET diem = diem - ? WHERE user_id=?', (so_diem, user_id)); conn.commit(); conn.close(); return True

# ==============================================================================
# PHẦN 2: BOT TELEGRAM HANDLERS
# ==============================================================================
@bot.message_handler(commands=['start'])
def start(message):
    u = message.from_user
    create_user(u.id, u.username, u.full_name)
    diem = get_diem(u.id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("🎲 Tạo bàn"), KeyboardButton("🎯 Đặt cược"))
    kb.row(KeyboardButton("💰 Nạp tiền"), KeyboardButton("💸 Rút tiền"))
    kb.row(KeyboardButton("👤 Hồ sơ"))
    if u.id == ADMIN_ID: kb.row(KeyboardButton("⚙️ Admin"))
    bot.reply_to(message, f"Chào {u.full_name}!\n💰 Điểm: {diem}\nChọn chức năng:", reply_markup=kb)

@bot.message_handler(commands=['congdiem'])
def cong_diem_admin(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        user_id, so_diem = int(parts[1]), int(parts[2])
        cong_diem(user_id, so_diem)
        bot.reply_to(message, f"✅ Đã cộng {so_diem} điểm cho user {user_id}.")
    except:
        bot.reply_to(message, "Cú pháp: /congdiem <user_id> <so_diem>")

@bot.message_handler(func=lambda m: m.text == "👤 Hồ sơ")
def ho_so(message):
    diem = get_diem(message.from_user.id)
    bot.reply_to(message, f"👤 ID: `{message.from_user.id}`\n💰 Điểm: {diem:,}", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "💰 Nạp tiền")
def nap_tien(message):
    msg = bot.reply_to(message, "Nhập số tiền muốn nạp (10.000 - 200.000 VNĐ):")
    bot.register_next_step_handler(msg, xu_ly_nap)

def xu_ly_nap(message):
    if message.text.startswith('/'): return
    try:
        so_tien = int(message.text.replace(".", "").replace(",", ""))
        if so_tien < 10000 or so_tien > 200000: raise ValueError
    except:
        bot.reply_to(message, "❌ Số tiền không hợp lệ."); return
        
    user_id = message.from_user.id
    ma_don = f"NAP{user_id}{so_tien}"
    qr_url = f"https://img.vietqr.io/image/{SEPAY_BANK_BIN}-{SEPAY_BANK_NUMBER}-compact2.png?amount={so_tien}&addInfo={ma_don}&accountName={SEPAY_ACCOUNT_NAME}"
    so_diem_nhan = int(so_tien / 10 * (1 - PHI_NAP))
    
    conn = get_conn()
    conn.execute('INSERT INTO giao_dich (user_id, so_tien, so_diem, ma_don) VALUES (?,?,?,?)', (user_id, so_tien, so_diem_nhan, ma_don))
    conn.commit(); conn.close()

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📲 Lấy mã QR", url=qr_url))
    bot.reply_to(message, f"✅ Tạo đơn nạp {so_tien:,}đ\n📝 Nội dung: {ma_don}\n💰 Nhận: {so_diem_nhan} điểm", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin")
def admin_menu(message):
    if message.from_user.id != ADMIN_ID: return
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("⬅️ Quay lại"))
    bot.reply_to(message, "⚙️ BẢNG ĐIỀU KHIỂN ADMIN\nGõ /congdiem <id> <diem> để cộng điểm.", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "⬅️ Quay lại")
def quay_lai(message):
    start(message)

# ==============================================================================
# PHẦN 3: CÀO API BANK
# ==============================================================================
BANK_API = "https://thueapibank.vn/historyapitpbv2/6ca255a6218e69fd95feb4348844a220"
processed_txs = set()

def check_bank():
    print("🚀 Đang cào API Bank...")
    while True:
        try:
            res = requests.get(BANK_API, timeout=15).json()
            for tx in res.get('transactions', []):
                tx_id = tx.get('transactionID')
                if tx.get('type') == 'IN' and tx_id not in processed_txs:
                    content = tx.get('description', '')
                    match = re.search(r'(NAP\d+)', content)
                    if match:
                        conn = get_conn()
                        gd = conn.execute('SELECT * FROM giao_dich WHERE ma_don=?', (match.group(1),)).fetchone()
                        if gd and gd['trang_thai'] == 'cho':
                            conn.execute('UPDATE giao_dich SET trang_thai="done" WHERE ma_don=?', (match.group(1),))
                            conn.execute('UPDATE users SET diem = diem + ? WHERE user_id=?', (gd['so_diem'], gd['user_id']))
                            conn.commit()
                            try:
                                bot.send_message(gd['user_id'], f"🎉 <b>NẠP THÀNH CÔNG</b>\nSố tiền: +{tx.get('amount'):,}đ\nĐiểm: +{gd['so_diem']:,}", parse_mode='HTML')
                            except: pass
                        conn.close()
                    processed_txs.add(tx_id)
        except Exception as e:
            pass
        time.sleep(10)

# ==============================================================================
# PHẦN 4: CÁC ENDPOINT FLASK (ĐÃ BỔ SUNG ĐẦY ĐỦ)
# ==============================================================================
@app.route('/health', methods=['GET'])
def health(): return "OK", 200

@app.route('/user', methods=['GET'])
def get_user_api():
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
def get_all_users_api():
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
def xem_ket_qua():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    conn = get_conn()
    ban = conn.execute("SELECT * FROM bans WHERE trang_thai='het_gio' ORDER BY ban_id DESC LIMIT 1").fetchone()
    conn.close()
    if ban and ban['ket_qua']:
        ket_qua_ma = ban['ket_qua'].split(',')
        ket_qua_chu = [TEN_CON_VAT[c] for c in ket_qua_ma]
        return jsonify({"ban_id": ban['ban_id'], "ket_qua_sap_ra": ket_qua_chu}), 200
    return jsonify({"message": "Không có bàn nào đang chờ."}), 200

@app.route('/adduser', methods=['GET', 'POST'])
def add_user_web():
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
# PHẦN 5: KHỞI CHẠY
# ==============================================================================
if __name__ == '__main__':
    init_db()
    def run_flask():
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=check_bank, daemon=True).start()
    print("🚀 Bot đang chạy...")
    bot.infinity_polling()
