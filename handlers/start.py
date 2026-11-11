from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID
from database import users as users_db
from database.db import get_conn

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        u = message.from_user
        users_db.create_user(u.id, u.username, u.full_name)
        diem = users_db.get_diem(u.id)
        
        # Tạo Menu chính
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(KeyboardButton("🎲 Tạo bàn"), KeyboardButton("🎯 Đặt cược"))
        kb.row(KeyboardButton("💰 Nạp tiền"), KeyboardButton("💸 Rút tiền"))
        kb.row(KeyboardButton("🏆 TOP NẠP"), KeyboardButton("👤 Hồ sơ"))
        kb.row(KeyboardButton("📖 Luật chơi"))
        
        if u.id == ADMIN_ID: 
            kb.row(KeyboardButton("⚙️ Admin"))
        
        bot.reply_to(
            message, 
            f"👋 Chào <b>{u.full_name}</b>!\n"
            f"💰 Điểm hiện tại: <b>{diem:,} điểm</b>\n\n"
            f"👇 Chọn chức năng bên dưới:", 
            reply_markup=kb, 
            parse_mode='HTML'
        )

    @bot.message_handler(func=lambda m: m.text == "🏆 TOP NẠP")
    def top_nap(message):
        conn = get_conn()
        # Truy vấn: Lấy tên và tổng số điểm đã nạp thành công, sắp xếp giảm dần, lấy top 10
        top = conn.execute('''
            SELECT u.ho_ten, SUM(g.so_diem) as tong_nap 
            FROM giao_dich g 
            JOIN users u ON g.user_id = u.user_id 
            WHERE g.trang_thai = 'done' 
            GROUP BY g.user_id 
            ORDER BY tong_nap DESC LIMIT 10
        ''').fetchall()
        conn.close()
        
        if not top:
            bot.reply_to(message, "Chưa có ai nạp tiền vào hệ thống.")
            return
            
        text = "🏆 <b>TOP 10 ĐẠI GIA NẠP TIỀN</b> 🏆\n"
        text += "-------------------------\n"
        
        # Vòng lặp in ra danh sách
        for i, u in enumerate(top, 1):
            # Thêm icon cho top 1, 2, 3
            icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
            text += f"{icon} <b>{u['ho_ten']}</b> - 💰 {u['tong_nap']:,} điểm\n"
            
        text += "-------------------------\n"
        text += "💡 Nạp nhiều để leo top nhé!"
        
        bot.reply_to(message, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "👤 Hồ sơ")
    def xem_ho_so(message):
        u = message.from_user
        diem = users_db.get_diem(u.id)
        
        text = (
            f"👤 <b>THÔNG TIN HỒ SƠ</b>\n"
            f"-------------------------\n"
            f"📛 Tên hiển thị: <b>{u.full_name}</b>\n"
            f"🆔 ID Telegram: <code>{u.id}</code>\n"
            f"🌐 Username: @{u.username if u.username else 'Không có'}\n"
            f"💰 Số dư điểm: <b>{diem:,} điểm</b>\n"
            f"💵 Quy đổi: {diem * 10:,} VNĐ\n"
        )
        bot.reply_to(message, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "📖 Luật chơi")
    def luat_choi(message):
        text = (
            f"📖 <b>LUẬT CHƠI BẦU CUA</b>\n"
            f"-------------------------\n"
            f"1️⃣ Người chơi đặt cược vào 1 trong 6 cửa: Bầu, Cua, Tôm, Cá, Gà, Nai.\n"
            f"2️⃣ Kết quả sẽ quay ra 3 con vật ngẫu nhiên.\n"
            f"3️⃣ Nếu cửa bạn đặt xuất hiện <b>n lần</b>, bạn sẽ ăn <b>n lần</b> tiền cược.\n"
            f"4️⃣ Nếu cửa bạn đặt không xuất hiện, bạn mất tiền cược.\n\n"
            f"👑 <b>LÀM CÁI (NHÀ CÁI):</b>\n"
            f"- Cần tối thiểu 100.000 điểm (1.000.000 VNĐ).\n"
            f"- Ăn tiền của người thua, trả tiền cho người thắng.\n\n"
            f"💳 <b>NẠP/RÚT:</b>\n"
            f"- Nạp tối thiểu 10.000đ, tối đa 200.000đ. Phí nạp 2%.\n"
            f"- Rút tiền: 1000 điểm = 10.000đ (Admin duyệt tay)."
        )
        bot.reply_to(message, text, parse_mode='HTML')

    @bot.message_handler(func=lambda m: m.text == "⬅️ Quay lại Menu")
    def quay_lai_menu(message):
        start(message)
