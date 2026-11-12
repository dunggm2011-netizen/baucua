const { Markup } = require('telegraf');
const config = require('../config');

const depositStates = {};

function setupDepositHandlers(bot) {
  bot.action('nap_tien', (ctx) => {
    const userId = ctx.from.id;
    depositStates[userId] = { step: 'waiting_deposit_amount' };

    ctx.editMessageText(
      `📥 **NẠP TIỀN TỰ ĐỘNG QUA VIETQR**\n\n` +
      `• Hạn mức: **Min 10.000đ - Max 200.000đ**\n` +
      `• Phí duy trì hệ thống: **2%**\n` +
      `• Tỷ lệ quy đổi: **10.000đ = 1.000 điểm**\n\n` +
      `👉 **Vui lòng nhập số tiền bạn muốn nạp vào khung chat (Ví dụ: 50000):**`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại Menu', 'main_menu')]])
      }
    );
  });

  bot.on('text', async (ctx, next) => {
    const userId = ctx.from.id;
    if (!depositStates[userId] || depositStates[userId].step !== 'waiting_deposit_amount') {
      return next();
    }

    const text = ctx.message.text.trim();
    const amount = parseInt(text, 10);

    if (isNaN(amount) || amount < 10000 || amount > 200000) {
      return ctx.reply('⚠️ Số tiền không hợp lệ! Vui lòng nhập số tiền từ **10.000** đến **200.000** VNĐ:', { parse_mode: 'Markdown' });
    }

    delete depositStates[userId];

    const content = `NAP ${userId}`;
    const qrUrl = `https://img.vietqr.io/image/${config.BANK_ID}-${config.BANK_ACCOUNT}-compact2.png?amount=${amount}&addInfo=${encodeURIComponent(content)}&accountName=${encodeURIComponent(config.BANK_OWNER_NAME)}`;

    const caption = 
      `📸 **MÃ QR NẠP TIỀN CỦA BẠN**\n\n` +
      `• Ngân hàng: **${config.BANK_ID}**\n` +
      `• Số tài khoản: \`${config.BANK_ACCOUNT}\`\n` +
      `• Chủ tài khoản: **${config.BANK_OWNER_NAME}**\n` +
      `• Số tiền: **${amount.toLocaleString()}đ**\n` +
      `• Nội dung chuyển khoản (Bắt buộc): \`${content}\`\n\n` +
      `⚠️ *Lưu ý: Hệ thống sẽ tự động cộng điểm sau 10-15 giây kể từ khi giao dịch thành công.*`;

    await ctx.replyWithPhoto(
      { url: qrUrl },
      {
        caption: caption,
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại Menu chính', 'main_menu')]])
      }
    );
  });
}

module.exports = { setupDepositHandlers };
