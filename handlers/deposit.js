const axios = require('axios');
const { readDB, writeDB } = require('../database');

// Thông tin tài khoản ngân hàng nhận tiền của chị (có thể thay đổi tùy ý)
const BANK_CONFIG = {
  BANK_ID: 'TPB', // Mã ngân hàng (TPB, VCB, MB,...)
  ACCOUNT_NO: '10004405178', // Số tài khoản nhận tiền
  ACCOUNT_NAME: 'NGUYEN CONG HOANG KHANG' // Tên chủ tài khoản
};

function setupDepositHandlers(bot) {
  // 1. Lệnh /nap hoặc nút nạp tiền: Tạo mã QR VietQR cho người chơi
  bot.command(['nap', 'naptien'], async (ctx) => {
    const args = ctx.message.text.split(' ');
    const amount = parseInt(args[1], 10);

    if (isNaN(amount) || amount < 10000) {
      return ctx.reply('⚠️ Vui lòng nhập số tiền muốn nạp hợp lệ (Tối thiểu 10.000 VNĐ).\nVí dụ: `/nap 50000`', { parse_mode: 'Markdown' });
    }

    const userId = ctx.from.id.toString();
    
    // Tạo mã nội dung chuyển khoản riêng biệt chứa chữ NAP + ID User + Số ngẫu nhiên
    const randomCode = Math.floor(100000 + Math.random() * 900000);
    const napCode = `NAP${userId}${randomCode}`;

    let db = readDB();
    if (!db.users) db.users = {};
    if (!db.users[userId]) db.users[userId] = { balance: 0 };

    // Lưu mã đang chờ nạp vào database của user
    db.users[userId].pendingCode = napCode;
    writeDB(db);

    // Link tạo ảnh QR VietQR tự động
    // Cú pháp chuẩn VietQR: https://img.vietqr.io/image/[BANK]-[ACC]-[TEMPLATE].png?amount=[MONEY]&addInfo=[CONTENT]&accountName=[NAME]
    const qrUrl = `https://img.vietqr.io/image/${BANK_CONFIG.BANK_ID}-${BANK_CONFIG.ACCOUNT_NO}-compact2.png?amount=${amount}&addInfo=${napCode}&accountName=${encodeURIComponent(BANK_CONFIG.ACCOUNT_NAME)}`;

    await ctx.replyWithPhoto(
      { url: qrUrl },
      {
        caption: 
          `💳 **QR NẠP TIỀN TỰ ĐỘNG**\n\n` +
          `• Số tiền: **${amount.toLocaleString()} VNĐ**\n` +
          `• Chủ tài khoản: \`${BANK_CONFIG.ACCOUNT_NAME}\`\n` +
          `• Số tài khoản: \`${BANK_CONFIG.ACCOUNT_NO}\` (${BANK_CONFIG.BANK_ID})\n\n` +
          `📝 Nội dung chuyển khoản bắt buộc:\n` +
          `👉 \`${napCode}\`\n\n` +
          `⚠️ **Lưu ý:** Quét mã QR trên app ngân hàng, nội dung chuyển khoản sẽ được điền tự động. Bot sẽ tự động cộng điểm sau 5-10 giây khi chuyển thành công!`,
        parse_mode: 'Markdown'
      }
    );
  });
}

// 2. Hàm tự động quét lịch sử ngân hàng từ thueapibank.vn và cộng điểm
async function checkDeposits(bot) {
  try {
    const apiUrl = 'https://thueapibank.vn/historyapitpbv2/73e4f7d402d32568163b9fd9f05e7be1'; 
    const response = await axios.get(apiUrl);
    
    if (response.data && response.data.status === 'success' && response.data.transactions) {
      let db = readDB();
      if (!db.historyTransactions) db.historyTransactions = []; // Chống cộng trùng lặp giao dịch
      let hasNewUpdate = false;

      for (const tx of response.data.transactions) {
        // Chỉ xử lý giao dịch tiền vào (IN) và chưa từng được xử lý
        if (tx.type === 'IN' && !db.historyTransactions.includes(tx.transactionID)) {
          const desc = tx.description.toUpperCase();
          
          // Dùng Regex bóc tách chữ NAP và mã theo sau
          const match = desc.match(/NAP([A-Z0-9]+)/);
          
          if (match) {
            const fullNapCode = match[0]; // VD: NAP8183105705
            const rawIdentifier = match[1]; 
            
            let targetUserId = null;
            
            // Tìm user đang chờ mã nạp này
            for (const [userId, uData] of Object.entries(db.users || {})) {
              if (uData.pendingCode === fullNapCode || rawIdentifier.includes(userId)) {
                targetUserId = userId;
                break;
              }
            }

            if (targetUserId) {
              const amount = tx.amount;
              const realAmount = Math.floor(amount * 0.98); // Trừ phí nạp 2%

              // Cộng điểm
              db.users[targetUserId].balance = (db.users[targetUserId].balance || 0) + realAmount;
              
              // Xóa mã chờ
              delete db.users[targetUserId].pendingCode;

              // Đánh dấu giao dịch đã xử lý
              db.historyTransactions.push(tx.transactionID);
              hasNewUpdate = true;

              // Gửi tin nhắn báo về Telegram cho khách
              try {
                await bot.telegram.sendMessage(
                  targetUserId,
                  `✅ **NẠP TIỀN THÀNH CÔNG!**\n\n` +
                  `• Mã giao dịch: \`${tx.transactionID}\`\n` +
                  `• Số tiền chuyển: **${amount.toLocaleString()} VNĐ**\n` +
                  `• Phí (2%): **${(amount - realAmount).toLocaleString()} VNĐ**\n` +
                  `• Điểm thực nhận: **+${realAmount.toLocaleString()} điểm**\n` +
                  `• Số dư hiện tại: **${db.users[targetUserId].balance.toLocaleString()} điểm**`,
                  { parse_mode: 'Markdown' }
                );
              } catch (err) {
                console.log(`Không gửi được tin nhắn cho user ${targetUserId}:`, err.message);
              }
            }
          }
        }
      }

      if (hasNewUpdate) {
        writeDB(db);
      }
    }
  } catch (error) {
    console.error('Lỗi khi quét lịch sử ngân hàng:', error.message);
  }
}

module.exports = { setupDepositHandlers, checkDeposits };
