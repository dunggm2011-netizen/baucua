const { Markup } = require('telegraf');
const { readDB, writeDB } = require('../database');
const config = require('../config');

const adminStates = {};

function setupAdminHandlers(bot) {
  function getAdminPanelKeyboard() {
    return Markup.inlineKeyboard([
      [Markup.button.callback('🎁 Tạo Giftcode', 'admin_create_gift'), Markup.button.callback('🎟️ Xem List Giftcode', 'admin_list_gifts')],
      [Markup.button.callback('👥 List All Users', 'admin_list_users')],
      [Markup.button.callback('🚫 Ban / Unban User', 'admin_ban_menu'), Markup.button.callback('💵 Cộng / Trừ tiền', 'admin_money_menu')],
      [Markup.button.callback('📢 Thông báo All', 'admin_broadcast')],
      [Markup.button.callback('🚪 Thoát chế độ Admin', 'admin_exit')]
    ]);
  }

  bot.action('admin_home', (ctx) => {
    const userId = ctx.from.id.toString();
    if (userId !== config.ADMIN_ID.toString()) return ctx.answerCbQuery('⚠️ Không có quyền!');
    delete adminStates[userId];
    ctx.editMessageText(`🔐 **BẢNG ĐIỀU KHIỂN ADMIN**\n\nChọn chức năng bên dưới:`, {
      parse_mode: 'Markdown',
      ...getAdminPanelKeyboard()
    });
  });

  bot.action('admin_exit', (ctx) => {
    const userId = ctx.from.id.toString();
    delete adminStates[userId];
    ctx.editMessageText('🚪 Đã thoát khỏi chế độ Admin.');
  });

  bot.action('admin_create_gift', (ctx) => {
    const userId = ctx.from.id.toString();
    adminStates[userId] = { step: 'waiting_gift_info' };
    ctx.editMessageText(
      `🎁 **TẠO GIFTCODE MỚI**\n\n` +
      `Nhập theo cú pháp:\n\`<Mã> <Điểm> <Số_Ngày> <Số_Lượng>\`\n\n_Ví dụ: TET2026 50000 7 10_`,
      { parse_mode: 'Markdown', ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại', 'admin_home')]]) }
    );
  });

  bot.action('admin_list_users', (ctx) => {
    const db = readDB();
    const users = db.users || {};
    const userIds = Object.keys(users);

    if (userIds.length === 0) return ctx.answerCbQuery('📭 Chưa có người chơi!', { show_alert: true });

    let text = `👥 **DANH SÁCH NGƯỜI CHƠI (${userIds.length})**\n\n`;
    userIds.slice(0, 15).forEach((uid, index) => {
      const u = users[uid];
      text += `${index + 1}. ID: \`${uid}\` | @${u.username || 'N/A'} | **${u.balance.toLocaleString()}đ**\n`;
    });

    ctx.editMessageText(text, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại', 'admin_home')]])
    });
  });

  bot.action('admin_list_gifts', (ctx) => {
    const db = readDB();
    const gifts = db.giftcodes || {};
    const codes = Object.keys(gifts);

    if (codes.length === 0) return ctx.answerCbQuery('📭 Không có giftcode nào!', { show_alert: true });

    let text = `🎟️ **DANH SÁCH GIFTCODE**\n\n`;
    let buttons = [];

    codes.forEach((code) => {
      const g = gifts[code];
      const usedCount = g.usedBy ? g.usedBy.length : 0;
      text += `• \`${code}\` | 💰 **${g.points.toLocaleString()}đ** | Dùng: ${usedCount}/${g.maxUses}\n`;
      buttons.push([Markup.button.callback(`🗑️ Xóa: ${code}`, `delete_gift_${code}`)]);
    });
    buttons.push([Markup.button.callback('« Quay lại', 'admin_home')]);

    ctx.editMessageText(text, { parse_mode: 'Markdown', ...Markup.inlineKeyboard(buttons) });
  });

  bot.action(/delete_gift_(.+)/, (ctx) => {
    const code = ctx.match[1];
    let db = readDB();
    if (db.giftcodes && db.giftcodes[code]) {
      delete db.giftcodes[code];
      writeDB(db);
      ctx.editMessageText(`✅ Đã xóa mã **${code}** thành công!`, {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại danh sách', 'admin_list_gifts')]])
      });
    }
  });

  bot.action('admin_ban_menu', (ctx) => {
    const userId = ctx.from.id.toString();
    adminStates[userId] = { step: 'waiting_ban_id' };
    ctx.editMessageText(`🚫 **BAN / UNBAN USER**\n\nNhập User ID cần khóa/mở khóa:`, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại', 'admin_home')]])
    });
  });

  bot.action('admin_money_menu', (ctx) => {
    const userId = ctx.from.id.toString();
    adminStates[userId] = { step: 'waiting_money_input' };
    ctx.editMessageText(
      `💵 **CỘNG / TRỪ TIỀN**\n\n` +
      `Nhập cú pháp: \`<UserID> <±Số điểm>\`\n` +
      `_Ví dụ:_ \`123456789 50000\` hoặc \`123456789 -20000\``,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại', 'admin_home')]])
      }
    );
  });

  bot.action('admin_broadcast', (ctx) => {
    const userId = ctx.from.id.toString();
    adminStates[userId] = { step: 'waiting_broadcast_text' };
    ctx.editMessageText(`📢 **THÔNG BÁO ALL**\n\nNhập nội dung thông báo:`, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại', 'admin_home')]])
    });
  });

  bot.on('text', async (ctx, next) => {
    const userId = ctx.from.id.toString();
    if (userId !== config.ADMIN_ID.toString() || !adminStates[userId]) return next();

    const state = adminStates[userId];
    const text = ctx.message.text.trim();

    if (state.step === 'waiting_gift_info') {
      delete adminStates[userId];
      const parts = text.split(/\s+/);
      if (parts.length < 4) return ctx.reply('⚠️ Sai cú pháp! Nhập: `<Mã> <Điểm> <Ngày> <Số_lượng>`');

      const code = parts[0].toUpperCase();
      const points = parseInt(parts[1], 10);
      const days = parseInt(parts[2], 10);
      const maxUses = parseInt(parts[3], 10);
      const expiresAt = Date.now() + (days * 24 * 60 * 60 * 1000);

      let db = readDB();
      if (!db.giftcodes) db.giftcodes = {};
      db.giftcodes[code] = { points, expiresAt, maxUses, usedBy: [] };
      writeDB(db);

      return ctx.reply(`✅ Tạo giftcode \`${code}\` thành công!`, { parse_mode: 'Markdown' });
    }

    if (state.step === 'waiting_broadcast_text') {
      delete adminStates[userId];
      let db = readDB();
      const userIds = Object.keys(db.users || {});
      for (const uid of userIds) {
        try { await bot.telegram.sendMessage(uid, `📢 **THÔNG BÁO TỪ HỆ THỐNG**\n\n${text}`, { parse_mode: 'Markdown' }); } catch (e) {}
      }
      return ctx.reply(`✅ Đã gửi thông báo thành công đến tất cả người chơi!`);
    }

    if (state.step === 'waiting_money_input') {
      delete adminStates[userId];
      const parts = text.split(/\s+/);
      if (parts.length < 2) return ctx.reply('⚠️ Sai cú pháp! Vui lòng nhập: `UserID SốĐiểm` (Ví dụ: `123456789 50000`)');

      const targetId = parts[0].trim();
      const amountChange = parseInt(parts[1].replace('+', ''), 10);

      let db = readDB();
      if (!db.users[targetId]) {
        db.users[targetId] = { balance: 0, username: 'Player' };
      }

      db.users[targetId].balance += amountChange;
      writeDB(db);
      return ctx.reply(`✅ Đã cộng/trừ điểm thành công cho User \`${targetId}\`!\n• Biến động: ${amountChange >= 0 ? '+' : ''}${amountChange.toLocaleString()} điểm\n• Số dư mới: **${db.users[targetId].balance.toLocaleString()} điểm**`, { parse_mode: 'Markdown' });
    }

    if (state.step === 'waiting_ban_id') {
      delete adminStates[userId];
      let db = readDB();
      if (!db.banned) db.banned = [];

      const targetId = text.trim();
      const index = db.banned.indexOf(targetId);
      if (index > -1) {
        db.banned.splice(index, 1);
        writeDB(db);
        return ctx.reply(`✅ Đã UNBAN User \`${targetId}\``, { parse_mode: 'Markdown' });
      } else {
        db.banned.push(targetId);
        writeDB(db);
        return ctx.reply(`🚫 Đã BAN User \`${targetId}\``, { parse_mode: 'Markdown' });
      }
    }

    return next();
  });
}

module.exports = { setupAdminHandlers };
