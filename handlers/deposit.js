const { Markup } = require('telegraf');
const { readDB, writeDB } = require('../database');
const config = require('../config');

const depositStates = {};

function setupDepositHandlers(bot) {
  bot.action('nap_tien', (ctx) => {
    const userId = ctx.from.id.toString();
    depositStates[userId] = { step: 'waiting_amount' };

    ctx.editMessageText(
      `💳 **HƯỚNG DẪN NẠP TIỀN TỰ ĐỘNG (Phí nạp: 2%)**\n\n` +
      `Vui lòng nhập số tiền VNĐ bạn muốn nạp vào khung chat (Ví dụ: \`50000\` VNĐ):\n` +
      `_Tỷ lệ quy đổi: 10.000 VNĐ = 1.000 Điểm (Áp dụng phí 2%)_`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại Menu', 'main_menu')]])
      }
    );
  });

  bot.on('text', async (ctx, next) => {
    const userId = ctx.from.id.toString();
    if (!depositStates[userId] || depositStates[userId].step !== 'waiting_amount') {
      return next();
    }

    const text = ctx.message.text.trim();
    const moneyAmount = parseInt(text, 10);

    if (isNaN(moneyAmount) || moneyAmount < 10000) {
      delete depositStates[userId];
      return ctx.reply('⚠️ Số tiền nạp tối thiểu là 10.000 VNĐ. Vui lòng bấm Nạp tiền lại!');
    }

    delete depositStates[userId];

    // Quy đổi điểm gốc: 10.000 VNĐ = 1.000 điểm (Tiền VNĐ chia 10)
    const basePoints = Math.floor(moneyAmount / 10);
    
    // Trừ 2% phí nạp, phần còn lại là số điểm thực nhận vào game
    const feePoints = Math.round(basePoints * 0.02);
    const finalPoints = basePoints - feePoints;

    const transferContent = `NAP${userId}`;
    const bankId = config.BANK_ID || 'TPBank'; 
    const accountNo = config.ACCOUNT_NO || '1000405178';
    const accountName = config.ACCOUNT_NAME || 'NGUYEN CONG HOANG KHANG';

    const qrUrl = `https://img.vietqr.io/image/${bankId}-${accountNo}-compact2.png?amount=${moneyAmount}&addInfo=${encodeURIComponent(transferContent)}&accountName=${encodeURIComponent(accountName)}`;

    let msg = `📥 **THÔNG TIN CHUYỂN KHOẢN NẠP TIỀN**\n\n` +
              `• Ngân hàng: \`${bankId}\`\n` +
              `• Số tài khoản: \`${accountNo}\`\n` +
              `• Chủ tài khoản: \`${accountName}\`\n` +
              `• Số tiền chuyển: **${moneyAmount.toLocaleString()} VNĐ**\n` +
              `• Điểm gốc: ${basePoints.toLocaleString()} điểm\n` +
              `• Phí nạp (2%): -${feePoints.toLocaleString()} điểm\n` +
              `• **Điểm thực nhận:** ⭐ **${finalPoints.toLocaleString()} điểm**\n\n` +
              `• Nội dung chuyển khoản (BẮT BUỘC): \`${transferContent}\`\n\n` +
              `⚠️ _Hệ thống sẽ tự động quét API và cộng ${finalPoints.toLocaleString()} điểm sau 15-30 giây khi nhận được tiền._`;

    try {
      await ctx.replyWithPhoto(qrUrl, {
        caption: msg,
        parse_mode: 'Markdown'
      });
    } catch (err) {
      await ctx.reply(msg, { parse_mode: 'Markdown' });
    }
  });
}

module.exports = { setupDepositHandlers };
