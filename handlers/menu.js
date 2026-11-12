const { Markup } = require('telegraf');
const { readDB, writeDB } = require('../database');
const config = require('../config');

function setupMenuHandlers(bot) {
  function getMainMenuKeyboard(userId) {
    const keyboardButtons = [
      [Markup.button.callback('🎲 Tạo bàn', 'taoban'), Markup.button.callback('🎮 Chọn bàn chơi', 'chon_ban')],
      [Markup.button.callback('💰 Nạp tiền', 'nap_tien'), Markup.button.callback('📤 Rút tiền', 'rut_tien')],
      [Markup.button.callback('👤 Thông tin TK', 'menu_acc'), Markup.button.callback('🏆 Top Nạp', 'top_nap')],
      [Markup.button.callback('🎁 Nhập Giftcode', 'nhap_giftcode'), Markup.button.callback('📞 CSKH', 'cskh')]
    ];

    if (userId.toString() === config.ADMIN_ID.toString()) {
      keyboardButtons.push([Markup.button.callback('🔐 Bảng Quản Trị Admin', 'admin_home')]);
    }

    return Markup.inlineKeyboard(keyboardButtons);
  }

  bot.start((ctx) => {
    const userId = ctx.from.id;
    let db = readDB();
    if (!db.users[userId]) {
      db.users[userId] = { balance: 0, username: ctx.from.username || 'Player' };
      writeDB(db);
    }

    ctx.reply(
      `🎲 **CHÀO MỪNG ĐẾN VỚI SÒNG BẦU CUA TELEGRAM** 🎲\n\n` +
      `Hệ thống giải trí uy tín - Làm cái tự do - Nạp rút tự động nhanh chóng.\n` +
      `Mời bạn chọn các chức năng bên dưới:`,
      { parse_mode: 'Markdown', ...getMainMenuKeyboard(userId) }
    );
  });

  bot.action('main_menu', (ctx) => {
    const userId = ctx.from.id;
    ctx.editMessageText(`🎲 **MENU CHÍNH** 🎲\nMời bạn chọn chức năng:`, {
      parse_mode: 'Markdown',
      ...getMainMenuKeyboard(userId)
    });
  });

  bot.action('menu_acc', (ctx) => {
    const userId = ctx.from.id;
    let db = readDB();
    const user = db.users[userId] || { balance: 0 };
    ctx.editMessageText(
      `👤 **THÔNG TIN TÀI KHOẢN**\n\n` +
      `• ID: \`${userId}\`\n` +
      `• Username: @${ctx.from.username || 'Không có'}\n` +
      `• Số dư hiện tại: **${user.balance.toLocaleString()} điểm**`,
      { parse_mode: 'Markdown', ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại Menu', 'main_menu')]]) }
    );
  });

  // Nút CSKH hiển thị tài khoản liên hệ
  bot.action('cskh', (ctx) => {
    ctx.editMessageText(
      `📞 **HỖ TRỢ KHÁCH HÀNG (CSKH)**\n\n` +
      `Mọi thắc mắc về nạp rút, khiếu nại vui lòng liên hệ trực tiếp:\n` +
      `👉 **Telegram:** @${config.CSKH_USERNAME}`,
      { parse_mode: 'Markdown', ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại Menu', 'main_menu')]]) }
    );
  });

  // Top Nạp
  bot.action('top_nap', (ctx) => {
    let db = readDB();
    const users = db.users || {};
    const sortedUsers = Object.entries(users).sort((a, b) => b[1].balance - a[1].balance).slice(0, 10);

    let text = `🏆 **BẢNG XẾP HẠNG TÀI PHÚ**\n\n`;
    sortedUsers.forEach(([uid, u], index) => {
      text += `${index + 1}. @${u.username || 'Player'} - **${u.balance.toLocaleString()} điểm**\n`;
    });

    ctx.editMessageText(text, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard([[Markup.button.callback('« Quay lại Menu', 'main_menu')]])
    });
  });

  // Chọn bàn chơi
  bot.action('chon_ban', (ctx) => {
    let db = readDB();
    const tables = db.tables || {};
    const tableIds = Object.keys(tables);

    if (tableIds.length === 0) {
      return ctx.answerCbQuery('⚠️ Hiện tại không có bàn chơi nào đang mở. Hãy tạo bàn mới!', { show_alert: true });
    }

    let buttons = [];
    tableIds.forEach((tableId, index) => {
      buttons.push([Markup.button.callback(`🎲 Tham gia Bàn #${index + 1} (Chủ xị: ${tables[tableId].hostId})`, `join_table_${tableId}`)]);
    });
    buttons.push([Markup.button.callback('« Quay lại Menu', 'main_menu')]);

    ctx.editMessageText(`🎮 **DANH SÁCH BÀN CHƠI ĐANG MỞ**\n\nChọn bàn bên dưới để tham gia cược:`, {
      parse_mode: 'Markdown',
      ...Markup.inlineKeyboard(buttons)
    });
  });

  bot.action(/join_table_(.+)/, (ctx) => {
    const tableId = ctx.match[1];
    let db = readDB();
    const table = db.tables[tableId];
    if (!table) return ctx.answerCbQuery('⚠️ Bàn chơi không còn tồn tại!', { show_alert: true });

    ctx.editMessageText(
      `🎲 **THAM GIA BÀN CHƠI**\n👑 Chủ xị: \`${table.hostId}\`\n⏳ Thời gian còn lại: ${table.timeLeft} giây\n\nChọn cửa cược bên dưới:`,
      {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([
          [Markup.button.callback('🦌 Nai', `bet_${tableId}_Nai`), Markup.button.callback(' Bầu', `bet_${tableId}_Bầu`), Markup.button.callback('🐔 Gà', `bet_${tableId}_Gà`)],
          [Markup.button.callback('🐟 Cá', `bet_${tableId}_Cá`), Markup.button.callback('🦀 Cua', `bet_${tableId}_Cua`), Markup.button.callback('🦐 Tôm', `bet_${tableId}_Tôm`)],
          [Markup.button.callback('« Quay lại Menu', 'main_menu')]
        ])
      }
    );
  });
}

module.exports = { setupMenuHandlers };
