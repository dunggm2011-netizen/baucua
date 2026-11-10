import os
import threading
import sqlite3
import json
import asyncio
from flask import Flask, request, jsonify, render_template_string
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ConversationHandler
)
from config import BOT_TOKEN, ADMIN_ID, ADMIN_KEY, DB_PATH
from database.db import init_db
import database.games as games_db
import database.users as users_db
from handlers import start, tao_ban, dat_cuoc, soc, admin, nap_tien, rut_tien

# ==========================================
# SỬA LỖI EVENT LOOP CHO PYTHON 3.14 TRÊN RENDER
# ==========================================
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
# ==========================================

# 1. KHỞI TẠO FLASK & TELEGRAM
flask_app = Flask(__name__)
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

async def text_handler(update: Update, context):
    text = update.message.text
    if text == "🎲 Tạo bàn": await tao_ban.tao_ban(update, context)
    elif text == "🎯 Đặt cược": await dat_cuoc.menu_dat_cuoc(update, context)
    elif text == "📖 Luật chơi": await start.luat_choi(update, context)
    elif text == "💰 Nạp tiền": await nap_tien.bat_dau_nap(update, context)
    elif text == "💸 Rút tiền": await rut_tien.bat_dau_rut(update, context)

def setup_bot():
    telegram_app.add_handler(CommandHandler("start", start.start))
    telegram_app.add_handler(CommandHandler("cuoc", dat_cuoc.menu_dat_cuoc))
    telegram_app.add_handler(CommandHandler("duyetrut", admin.duyet_rut))
    telegram_app.add_handler(CommandHandler("congdiem", admin.cong_diem_admin))
    
    nap_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Nạp tiền$"), nap_tien.bat_dau_nap)],
        states={nap_tien.NAP_NHAP_SO_TIEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, nap_tien.xu_ly_so_tien)]},
        fallbacks=[CommandHandler("huy", nap_tien.huy)]
    )
    telegram_app.add_handler(nap_conv)

    rut_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💸 Rút tiền$"), rut_tien.bat_dau_rut)],
        states={
            rut_tien.RUT_NHAP_DIEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, rut_tien.xu_ly_diem_rut)],
            rut_tien.RUT_NHAP_STK: [MessageHandler(filters.TEXT & ~filters.COMMAND, rut_tien.xu_ly_stk)],
        },
        fallbacks=[CommandHandler("huy", rut_tien.huy)]
    )
    telegram_app.add_handler(rut_conv)
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    telegram_app.add_handler(CallbackQueryHandler(dat_cuoc.xu_ly_cuoc, pattern="^cuoc_"))
    telegram_app.add_handler(CallbackQueryHandler(soc.xu_ly_soc, pattern="^soc_"))

# 2. CÁC ENDPOINT FLASK
@flask_app.route('/sepay-webhook', methods=['POST'])
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

@flask_app.route('/health', methods=['GET'])
def health(): return "OK", 200

def get_user_data(user_id=None, username=None):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; c = conn.cursor()
    if user_id: c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    elif username: c.execute("SELECT * FROM users WHERE username = ?", (username,))
    else: conn.close(); return None
    row = c.fetchone(); conn.close(); return dict(row) if row else None

@flask_app.route('/user', methods=['GET'])
def get_user_json():
    if request.args.get('key') != ADMIN_KEY: return jsonify({"error": "403 Forbidden"}), 403
    user_id, username = request.args.get('id'), request.args.get('username')
    if not user_id and not username: return jsonify({"error": "Thiếu ?id= hoặc ?username="}), 400
    user_data = get_user_data(user_id, username)
    if user_data:
        user_data['user_id'] = str(user_data['user_id']); return jsonify(user_data), 200
    return jsonify({"error": "Không tìm thấy user"}), 404

@flask_app.route('/adduser', methods=['GET', 'POST'])
def add_user_html():
    if request.args.get('key') != ADMIN_KEY: return "403 Forbidden: Sai mã bảo mật", 403
    message = ""
    if request.method == 'POST':
        try:
            data = json.loads(request.form.get('user_json', ''))
            if 'user_id' not in data: message = "❌ Lỗi: JSON thiếu trường 'user_id'"
            else:
                conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                c.execute('''INSERT OR REPLACE INTO users (user_id, username, ho_ten, diem) VALUES (?, ?, ?, ?)''', 
                          (int(data['user_id']), data.get('username'), data.get('ho_ten'), data.get('diem', 0)))
                conn.commit(); conn.close()
                message = f"✅ Đã cập nhật user {data['user_id']} với {data.get('diem', 0)} điểm!"
        except Exception as e: message = f"❌ Lỗi JSON: {str(e)}"
    html = """
    <!DOCTYPE html><html><head><title>Admin - Phục hồi User</title><meta charset="utf-8">
    <style>body{font-family:Arial;padding:20px;max-width:600px;margin:auto}textarea{width:100%;height:200px;margin-bottom:10px;font-family:monospace}button{padding:10px 20px;background:#28a745;color:white;border:none;cursor:pointer;border-radius:5px}.message{padding:10px;margin-bottom:10px;background:#e9ecef;border-radius:5px}</style>
    </head><body><h2>Phục hồi dữ liệu User</h2>{% if message %}<div class="message">{{ message }}</div>{% endif %}
    <form method="POST"><p>Dán nội dung JSON vào đây:</p><textarea name="user_json" placeholder='{"user_id": "123", "diem": 5000}'></textarea><button type="submit">Lưu vào Database</button></form></body></html>
    """
    return render_template_string(html, message=message)

# 3. HÀM CHẠY CHÍNH
if __name__ == '__main__':
    init_db()
    setup_bot()

    if os.environ.get('RENDER'):
        port = int(os.environ.get('PORT', 10000))
        webhook_url = os.environ.get('https://baucuabita.onrender.com')
        print(f"🚀 Chạy Webhook Mode trên cổng {port}...")
        
        # Chạy bot với Webhook
        telegram_app.run_webhook(
            listen="0.0.0.0", 
            port=port, 
            url_path=BOT_TOKEN, 
            webhook_url=f"{webhook_url}/{BOT_TOKEN}", 
            allowed_updates=Update.ALL_TYPES
        )
    else:
        print("🚀 Chạy Polling Mode...")
        # Chạy Flask ở một luồng riêng
        def run_flask():
            flask_app.run(host='0.0.0.0', port=5000)
        
        threading.Thread(target=run_flask, daemon=True).start()
        telegram_app.run_polling()
