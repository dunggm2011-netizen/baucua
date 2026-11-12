const { Markup } = require('telegraf');
const { readDB, writeDB } = require('../database');

const giftStates = {};

function setupGiftcodeHandlers(bot) {
  bot.action('nhap_giftcode', (ctx) => {
    const userId = ctx.from.id.toString();
    giftStates[userId] = { step: 'waiting_code' };

    ctx.editMessageText(
      `🎁 **NHẬP MÃ GIFTCODE**\n\nVui lòng gửi mã giftcode của bạn vào khung chat:`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại Menu', 'main_menu')]])
      }
    );
  });

  bot.on('text', async (ctx, next) => {
    const userId = ctx.from.id.toString();
    if (!giftStates[userId] || giftStates[userId].step !== 'waiting_code') {
      return next();
    }

    delete giftStates[userId];
    const code = ctx.message.text.trim().toUpperCase();

    let db = readDB();
    if (!db.giftcodes || !db.giftcodes[code]) {
      return ctx.reply('⚠️ Mã giftcode không tồn tại hoặc đã hết hạn!');
    }

    const gift = db.giftcodes[code];

    if (Date.now() > gift.expiresAt) {
      return ctx.reply('⚠️ Mã giftcode này đã hết hạn sử dụng!');
    }

    if (!gift.usedBy) gift.usedBy = [];
    if (gift.usedBy.includes(userId)) {
      return ctx.reply('⚠️ Bạn đã sử dụng mã giftcode này rồi!');
    }

    if (gift.usedBy.length >= gift.maxUses) {
      return ctx.reply('⚠️ Mã giftcode này đã hết lượt sử dụng!');
    }

    if (!db.users[userId]) {
      db.users[userId] = { balance: 0, username: ctx.from.username || 'Player' };
    }

    db.users[userId].balance += gift.points;
    gift.usedBy.push(userId);
    writeDB(db);

    return ctx.reply(
      `🎉 **NHẬP GIFTCODE THÀNH CÔNG!**\n\n` +
      `• Mã code: \`${code}\`\n` +
      `• Nhận được: **+${gift.points.toLocaleString()} điểm**\n` +
      `• Số dư hiện tại: **${db.users[userId].balance.toLocaleString()} điểm**`,
      { parse_mode: 'Markdown' }
    );
  });
}

module.exports = { setupGiftcodeHandlers };
