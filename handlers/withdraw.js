const { Markup } = require('telegraf');
const { readDB, writeDB } = require('../database');
const config = require('../config');

const userStates = {};

function setupWithdrawHandlers(bot) {
  bot.action('rut_tien', (ctx) => {
    const userId = ctx.from.id;
    userStates[userId] = { step: 'waiting_withdraw_info' };

    ctx.editMessageText(
      `📤 **YÊU CẦU RÚT TIỀN THỦ CÔNG**\n\n` +
      `Vui lòng gửi thông tin theo cú pháp sau trong khung chat:\n` +
      `\`Số_điểm | Tên_Ngân_Hàng | Số_TK | Tên_Chủ_TK\`\n\n` +
      `_Ví dụ:_\n\`50000 | VCB | 0123456789 | NGUYEN VAN A\`\n\n` +
      `*(Tỷ lệ quy đổi: 1.000 điểm = 10.000 VNĐ)*`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại', 'main_menu')]])
      }
    );
  });

  bot.on('text', async (ctx, next) => {
    const userId = ctx.from.id;
    if (!userStates[userId] || userStates[userId].step !== 'waiting_withdraw_info') {
      return next();
    }

    const text = ctx.message.text.trim();
    const parts = text.split('|').map(p => p.trim());

    if (parts.length < 4) {
      return ctx.reply('⚠️ Sai cú pháp! Vui lòng nhập đúng định dạng:\n`Số_điểm | Ngân_Hàng | Số_TK | Chủ_TK`', { parse_mode: 'Markdown' });
    }

    const pointsToWithdraw = parseInt(parts[0], 10);
    const bankName = parts[1];
    const bankAccount = parts[2];
    const accountName = parts[3];

    if (isNaN(pointsToWithdraw) || pointsToWithdraw <= 0) {
      return ctx.reply('⚠️ Số điểm rút không hợp lệ!');
    }

    let db = readDB();
    const user = db.users[userId];

    if (!user || user.balance < pointsToWithdraw) {
      delete userStates[userId];
      return ctx.reply(`⚠️ Số dư của bạn không đủ! Số dư hiện tại: **${user ? user.balance : 0} điểm**`, { parse_mode: 'Markdown' });
    }

    user.balance -= pointsToWithdraw;
    writeDB(db);
    delete userStates[userId];

    ctx.reply(`✅ **Đã gửi yêu cầu rút tiền thành công!**\nAdmin đang xử lý và sẽ chuyển khoản cho bạn sớm nhất.`);

    const requestDetails = 
      `🚨 **CÓ YÊU CẦU RÚT TIỀN MỚI!**\n\n` +
      `• User ID: \`${userId}\`\n` +
      `• Username: @${ctx.from.username || 'Không có'}\n` +
      `• Số điểm rút: **${pointsToWithdraw.toLocaleString()} điểm** (~${(pointsToWithdraw * 10).toLocaleString()} VNĐ)\n` +
      `• Ngân hàng: ${bankName}\n` +
      `• Số TK: \`${bankAccount}\`\n` +
      `• Chủ TK: ${accountName}`;

    try {
      await bot.telegram.sendMessage(
        config.ADMIN_ID,
        requestDetails,
        {
          parse_mode: 'Markdown',
          ...Markup.inlineKeyboard([
            [
              Markup.button.callback('✅ Duyệt', `approve_wd_${userId}_${pointsToWithdraw}`),
              Markup.button.callback('❌ Từ chối', `reject_wd_${userId}_${pointsToWithdraw}`)
            ]
          ])
        }
      );
    } catch (err) {
      console.error('Không gửi được tin nhắn cho Admin:', err.message);
    }
  });

  bot.action(/approve_wd_(\d+)_(\d+)/, async (ctx) => {
    const adminId = ctx.from.id.toString();
    if (adminId !== config.ADMIN_ID.toString()) {
      return ctx.answerCbQuery('⚠️ Bạn không có quyền thao tác này!', { show_alert: true });
    }

    const userId = ctx.match[1];
    const points = ctx.match[2];

    await ctx.editMessageText(ctx.callbackQuery.message.text + `\n\n✅ **Trạng thái:** ĐÃ DUYỆT`, { parse_mode: 'Markdown' });

    bot.telegram.sendMessage(
      userId,
      `🎉 **Yêu cầu rút ${parseInt(points).toLocaleString()} điểm của bạn đã được Admin duyệt!**`
    );

    ctx.answerCbQuery('Đã duyệt đơn rút tiền thành công!');
  });

  bot.action(/reject_wd_(\d+)_(\d+)/, async (ctx) => {
    const adminId = ctx.from.id.toString();
    if (adminId !== config.ADMIN_ID.toString()) {
      return ctx.answerCbQuery('⚠️ Bạn không có quyền thao tác này!', { show_alert: true });
    }

    const userId = ctx.match[1];
    const points = parseInt(ctx.match[2], 10);

    let db = readDB();
    if (db.users[userId]) {
      db.users[userId].balance += points;
      writeDB(db);
    }

    await ctx.editMessageText(ctx.callbackQuery.message.text + `\n\n❌ **Trạng thái:** ĐÃ TỪ CHỐI (Đã hoàn điểm)`, { parse_mode: 'Markdown' });

    bot.telegram.sendMessage(
      userId,
      `❌ **Yêu cầu rút ${points.toLocaleString()} điểm đã bị từ chối.** Điểm đã được hoàn lại.`
    );

    ctx.answerCbQuery('Đã từ chối và hoàn điểm cho khách!');
  });
}

module.exports = { setupWithdrawHandlers };
