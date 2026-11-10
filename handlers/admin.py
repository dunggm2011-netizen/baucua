from config import ADMIN_ID
import database.users as users_db

def register_handlers(bot):
    @bot.message_handler(commands=['congdiem'])
    def cong_diem_admin(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            parts = message.text.split()
            user_id, so_diem = int(parts[1]), int(parts[2])
        except:
            bot.reply_to(message, "Cú pháp: /congdiem <user_id> <so_diem>")
            return
            
        users_db.cong_diem(user_id, so_diem)
        bot.reply_to(message, f"Đã cộng {so_diem} điểm cho {user_id}.")
        
        try:
            bot.send_message(user_id, f"🎁 Bạn đã được Admin cộng {so_diem} điểm vào tài khoản.")
        except:
            pass

    @bot.message_handler(commands=['trudiem'])
    def tru_diem_admin(message):
        if message.from_user.id != ADMIN_ID: return
        try:
            parts = message.text.split()
            user_id, so_diem = int(parts[1]), int(parts[2])
        except:
            bot.reply_to(message, "Cú pháp: /trudiem <user_id> <so_diem>")
            return
            
        if users_db.tru_diem(user_id, so_diem):
            bot.reply_to(message, f"✅ Đã trừ {so_diem} điểm của user {user_id}.")
        else:
            bot.reply_to(message, f"❌ User {user_id} không đủ điểm để trừ.")
