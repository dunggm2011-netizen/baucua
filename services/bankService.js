const axios = require('axios');
const { readDB, writeDB } = require('../database');
const config = require('../config');

async function checkBankTransactions(bot) {
  try {
    const response = await axios.get(config.BANK_API_URL);
    
    if (response.data.status !== 'success' || !response.data.transactions) {
      return;
    }

    const transactions = response.data.transactions;
    let db = readDB();

    if (!db.processedTxs) db.processedTxs = [];

    for (const tx of transactions) {
      if (tx.type !== 'IN') continue;

      const txId = tx.transactionID;
      const rawAmount = tx.amount;
      const description = tx.description || '';

      if (db.processedTxs.includes(txId)) continue;

      const match = description.match(/NAP\s+(\d+)/i);
      if (match) {
        const userId = match[1];

        if (rawAmount >= 10000 && rawAmount <= 200000) {
          const fee = rawAmount * 0.02;
          const netAmount = rawAmount - fee;
          const pointsToAdd = Math.floor(netAmount * 0.1);

          if (!db.users[userId]) {
            db.users[userId] = { balance: 0, username: 'Player' };
          }

          db.users[userId].balance += pointsToAdd;
          db.processedTxs.push(txId);
          if (db.processedTxs.length > 500) db.processedTxs.shift();

          writeDB(db);

          await bot.telegram.sendMessage(
            userId,
            `✅ **NẠP TIỀN THÀNH CÔNG!**\n\n` +
            `• Mã giao dịch: \`${txId}\`\n` +
            `• Số tiền gửi: \`${rawAmount.toLocaleString()}đ\`\n` +
            `• Phí hệ thống (2%): \`${fee.toLocaleString()}đ\`\n` +
            `• Thực nhận: **+${pointsToAdd.toLocaleString()} điểm**\n` +
            `• Số dư hiện tại: **${db.users[userId].balance.toLocaleString()} điểm**`,
            { parse_mode: 'Markdown' }
          );

          console.log(`[BANK AUTO] Đã cộng ${pointsToAdd} điểm cho User ${userId} từ GD ID: ${txId}`);
        }
      }
    }
  } catch (error) {
    console.error('Lỗi kết nối API thueapibank.vn:', error.message);
  }
}

module.exports = { checkBankTransactions };
