from config import ADMIN_ID
import database.users as users_db
from database.db import get_conn

def register_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "📊 Xem danh sách User")
    def xem_danh_sach_user(message):
        if message.from_user.id != ADMIN_ID: return
        
        conn = get_conn()
        users = conn.execute('SELECT user_id, ho_ten, diem FROM users ORDER BY diem DESC LIMIT 20').fetchall()
        conn.close()
        
        if not users:
            bot.reply_to(message, "Chưa có người chơi nào.")
            return
            
        text = "📊 **TOP 20 NGƯỜI CHƠI (Theo điểm):**\n\n"
        for u in users:
            text += f"👤 {u['ho_ten']} (`{u['user_id']}`) - 💰 {u['diem']:,} điểm\n"
            
        bot.reply_to(message, text, parse_mode='Markdown')

    @bot.message_handler(func=lambda m: m.text == "📋 Xem yêu cầu rút")
    def xem_yeu_cau_rut(message):
        if message.from_user.id != ADMIN_ID: return
        
        conn = get_conn()
        # Lấy các yêu cầu đang chờ duyệt
        reqs = conn.execute("SELECT * FROM yeu_cau_rut WHERE trang_thai='cho_duyet'").fetchall()
        conn.close()
        
        if not reqs:
            bot.reply_to(message, "✅ Không có yêu cầu rút nào đang chờ duyệt.")
            return
            
        text = "📋 **YÊU CẦU RÚT ĐANG CHỜ:**\n\n"
        for r in reqs:
            text += f"🆔 Mã: `{r['id']}`\n👤 User: `{r['user_id']}`\n💸 Rút: {r['so_diem']} điểm\n🏦 STK: {r['stk']}\n👉 Duyệt: `/duyetrut {r['id']}`\n👉 Từ chối: `/tuchoi {r['id']}`\n----------------\n"
            
        bot.reply_to(message, text, parse_mode='Markdown')
    
    # ... (Các lệnh /congdiem, /trudiem giữ nguyên như cũ)
