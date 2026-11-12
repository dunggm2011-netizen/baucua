const axios = require('axios');
const { readDB, writeDB } = require('../database'); // Đường dẫn tới file quản lý database JSON của chị

// Hàm quét lịch sử giao dịch ngân hàng từ thueapibank.vn
async function checkBankTransactions(bot) {
  try {
    // Link API lịch sử ngân hàng TPBank của chị
    const apiUrl = 'https://thueapibank.vn/historyapitpbv2/73e4f7d402d32568163b9fd9f05e7be1'; 
    const response = await axios.get(apiUrl);
    
    if (response.data && response.data.status === 'success' && response.data.transactions) {
      let db = readDB();
      
      // Khởi tạo mảng lưu lịch sử các transactionID đã xử lý để tránh cộng trùng điểm
      if (!db.historyTransactions) {
        db.historyTransactions = [];
      }
      
      let hasNewUpdate = false;

      // Duyệt qua từng giao dịch trả về từ API
      for (const tx of response.data.transactions) {
        // Chỉ xử lý giao dịch tiền vào (type === 'IN') và giao dịch chưa từng được xử lý trước đó
        if (tx.type === 'IN' && !db.historyTransactions.includes(tx.transactionID)) {
          const desc = tx.description ? tx.description.toUpperCase() : '';
          
          // Dùng Regex tìm chữ NAP đi kèm chuỗi mã phía sau (Ví dụ: NAP8183105705)
          const match = desc.match(/NAP([A-Z0-9]+)/);
          
          if (match) {
            const fullNapCode = match[0]; // Cả cụm VD: NAP8183105705
            const rawIdentifier = match[1]; // Phần mã/ID theo sau chữ NAP
            
            let targetUserId = null;
            
            // Quét danh sách user trong DB xem ai đang sở hữu pendingCode khớp hoặc ID nằm trong chuỗi
            if (db.users) {
              for (const [userId, uData] of Object.entries(db.users)) {
                if (uData.pendingCode === fullNapCode || rawIdentifier.includes(userId)) {
                  targetUserId = userId;
                  break;
                }
              }
            }

            // Nếu tìm đúng user đang chờ nạp
            if (targetUserId) {
              const amount = tx.amount;
              // Trừ phí nạp tự động 2% (hoặc điều chỉnh tỷ lệ tùy ý chị)
              const realAmount = Math.floor(amount * 0.98); 

              // Cộng điểm vào số dư của user
              db.users[targetUserId].balance = (db.users[targetUserId].balance || 0) + realAmount;
              
              // Xóa mã chờ nạp để user không dùng lại mã cũ
              delete db.users[targetUserId].pendingCode;

              // Đánh dấu transactionID này đã được xử lý xong
              db.historyTransactions.push(tx.transactionID);
              hasNewUpdate = true;

              // Gửi tin nhắn thông báo thành công về Telegram cho người chơi
              try {
                await bot.telegram.sendMessage(
                  targetUserId,
                  `✅ **NẠP TIỀN THÀNH CÔNG!**\n\n` +
                  `• Mã giao dịch: \`${tx.transactionID}\`\n` +
                  `• Số tiền chuyển: **${amount.toLocaleString()} VNĐ**\n` +
                  `• Phí giao dịch (2%): **${(amount - realAmount).toLocaleString()} VNĐ**\n` +
                  `• Điểm thực nhận: **+${realAmount.toLocaleString()} điểm**\n` +
                  `• Số dư hiện tại: **${db.users[targetUserId].balance.toLocaleString()} điểm**`,
                  { parse_mode: 'Markdown' }
                );
                console.log(`[AUTO-DEPOSIT] Đã cộng ${realAmount} điểm cho user ${targetUserId} từ GD ${tx.transactionID}`);
              } catch (err) {
                console.log(`Không gửi được tin nhắn Telegram cho user ${targetUserId}:`, err.message);
              }
            }
          }
        }
      }

      // Lưu lại database nếu có thay đổi (cập nhật số dư và lịch sử giao dịch đã quét)
      if (hasNewUpdate) {
        writeDB(db);
      }
    }
  } catch (error) {
    console.error('❌ Lỗi khi quét lịch sử ngân hàng trong bankService:', error.message);
  }
}

module.exports = { checkBankTransactions };
