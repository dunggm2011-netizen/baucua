from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import users as users_db

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        u = message.from_user
        users_db.create_user(u.id, u.username, u.full_name)
        diem = users_db.get_diem(u.id)
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("🎲 Tạo bàn"), KeyboardButton("🎯 Đặt cược"))
        kb.row(KeyboardButton("💰 Nạp tiền"), KeyboardButton("💸 Rút tiền"))
        kb.row(KeyboardButton("👤 Hồ sơ"))
        if u.id == ADMIN_ID: kb.row(KeyboardButton("⚙️ Admin"))
        bot.reply_to(message, f"Chào {u.full_name}!\n💰 Điểm: {diem}\nChọn chức năng:", reply_markup=kb)
