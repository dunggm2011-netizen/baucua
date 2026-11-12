const axios = require('axios');
const { readDB, writeDB } = require('./database');

// Hàm kiểm tra và xử lý nạp tiền tự động
async function checkDeposits(bot) {
  try {
    // Thay link API và token của chị vào đây (hoặc lấy từ biến môi trường/config)
    const apiUrl = 'https://thueapibank.vn/historyapitpbv2/73e4f7d402d32568163b9fd9f05e7be1'; 
    const response = await axios.get(apiUrl);
    
    if (response.data && response.data.status === 'success' && response.data.transactions) {
      let db = readDB();
      if (!db.historyTransactions) db.historyTransactions = []; // Lưu các mã GD đã xử lý để tránh cộng trùng
      let hasNewUpdate = false;

      for (const tx of response.data.transactions) {
        // Chỉ xử lý giao dịch tiền vào (IN) và chưa từng được xử lý trước đó
        if (tx.type === 'IN' && !db.historyTransactions.includes(tx.transactionID)) {
          const desc = tx.description.toUpperCase();
          
          // Dùng Regex tìm chữ NAP đi kèm theo các ký tự phía sau (ví dụ: NAP8183105705)
          const match = desc.match(/NAP([A-Z0-9]+)/);
          
          if (match) {
            const fullNapCode = match[0]; // VD: NAP8183105705
            const rawIdentifier = match[1]; // Phần ID hoặc mã theo sau chữ NAP
            
            // Tìm xem user nào trong DB đang chờ mã này (hoặc lưu mã nạp kèm userId lúc tạo QR)
            // Ở đây em hỗ trợ tìm user theo ID hoặc lưu trực tiếp mã nạp của user
            let targetUserId = null;
            
            // Duyệt danh sách user xem có ai khớp mã nạp đang chờ không
            for (const [userId, uData] of Object.entries(db.users || {})) {
              // Giả sử trong user data chị lưu pendingDepositCode hoặc check theo ID nằm trong mã
              if (uData.pendingCode === fullNapCode || rawIdentifier.includes(userId)) {
                targetUserId = userId;
                break;
              }
            }

            if (targetUserId) {
              const amount = tx.amount;
              // Trừ phí nạp 2% (như chị đã cấu hình trước đó)
              const realAmount = Math.floor(amount * 0.98); 

              // Cộng điểm cho user
              db.users[targetUserId].balance = (db.users[targetUserId].balance || 0) + realAmount;
              
              // Xóa mã chờ nạp để tránh dùng lại
              delete db.users[targetUserId].pendingCode;

              // Đánh dấu giao dịch này đã xử lý
              db.historyTransactions.push(tx.transactionID);
              hasNewUpdate = true;

              // Gửi tin nhắn thông báo thành công về Telegram cho khách
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
                console.log(`Không gửi được tin nhắn Telegram cho user ${targetUserId}:`, err.message);
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

module.exports = { checkDeposits };
