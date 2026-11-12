const { Markup } = require('telegraf');
const { readDB, writeDB } = require('../database');
const fs = require('fs');
const path = require('path');

const ANIMALS = ['Nai', 'Bầu', 'Gà', 'Cá', 'Cua', 'Tôm'];

const ANIMAL_IMAGES = {
  'Nai': 'nai.jpg',
  'Bầu': 'bau.jpg',
  'Gà': 'ga.jpg',
  'Cá': 'ca.jpg',
  'Cua': 'cua.jpg',
  'Tôm': 'tom.jpg'
};

function setupGameHandlers(bot) {
  bot.action('taoban', async (ctx) => {
    const userId = ctx.from.id;
    let db = readDB();
    const userBalance = db.users[userId]?.balance || 0;

    if (userBalance < 1000000) {
      return ctx.answerCbQuery('⚠️ Bạn cần tối thiểu 1.000.000 điểm để làm cái!', { show_alert: true });
    }

    const tableId = `table_${Date.now()}`;
    const preGeneratedResult = [
      ANIMALS[Math.floor(Math.random() * ANIMALS.length)],
      ANIMALS[Math.floor(Math.random() * ANIMALS.length)],
      ANIMALS[Math.floor(Math.random() * ANIMALS.length)]
    ];

    db.tables[tableId] = {
      hostId: userId,
      status: 'betting',
      bets: {},
      preResult: preGeneratedResult,
      timeLeft: 50
    };
    writeDB(db);

    const sentMsg = await ctx.editMessageText(buildTableText(tableId, db.tables[tableId]), {
      parse_mode: 'Markdown',
      ...getTableKeyboard(tableId)
    });

    db.tables[tableId].chatId = ctx.chat.id;
    db.tables[tableId].messageId = sentMsg.message_id;
    writeDB(db);

    startCountdown(bot, tableId);
  });

  function buildTableText(tableId, table) {
    return `🎲 **BÀN BẦU CUA ĐANG MỞ CƯỢC**\n` +
           `👑 Chủ xị: \`${table.hostId}\`\n` +
           `⏳ **Thời gian còn lại: ${table.timeLeft} giây**\n\n` +
           `_Luật: Min cược 100 - Max 100.000 điểm_\n👉 Chọn cửa cược bên dưới:`;
  }

  function getTableKeyboard(tableId) {
    return Markup.inlineKeyboard([
      [Markup.button.callback('🦌 Nai', `bet_${tableId}_Nai`), Markup.button.callback(' Bầu', `bet_${tableId}_Bầu`), Markup.button.callback('🐔 Gà', `bet_${tableId}_Gà`)],
      [Markup.button.callback('🐟 Cá', `bet_${tableId}_Cá`), Markup.button.callback('🦀 Cua', `bet_${tableId}_Cua`), Markup.button.callback('🦐 Tôm', `bet_${tableId}_Tôm`)],
      [Markup.button.callback('⚡ Sóc ngay (Chủ xị)', `roll_${tableId}`)]
    ]);
  }

  function startCountdown(bot, tableId) {
    const timer = setInterval(async () => {
      let db = readDB();
      const table = db.tables[tableId];

      if (!table || table.status !== 'betting') {
        clearInterval(timer);
        return;
      }

      table.timeLeft -= 5;

      if (table.timeLeft <= 0) {
        clearInterval(timer);
        await executeRoll(bot, tableId, true);
      } else {
        writeDB(db);
        try {
          await bot.telegram.editMessageText(
            table.chatId,
            table.messageId,
            null,
            buildTableText(tableId, table),
            { parse_mode: 'Markdown', ...getTableKeyboard(tableId) }
          );
        } catch (err) {}
      }
    }, 5000);
  }

  bot.action(/bet_(.+)_(.+)/, (ctx) => {
    const tableId = ctx.match[1];
    const choice = ctx.match[2];
    let db = readDB();
    if (!db.tables[tableId] || db.tables[tableId].status !== 'betting') {
      return ctx.answerCbQuery('⚠️ Bàn chơi đã kết thúc!', { show_alert: true });
    }
    ctx.answerCbQuery(`Đã chọn ${choice}. Vui lòng nhập số điểm cược trong khung chat (100 - 100k):`);
  });

  bot.on('text', (ctx, next) => {
    // Xử lý cược nhanh khi user gửi số điểm
    const text = ctx.message.text.trim();
    const amount = parseInt(text, 10);
    if (isNaN(amount) || amount < 100 || amount > 100000) return next();
    // Logic cược có thể mở rộng ở đây nếu người chơi gửi số điểm sau khi bấm nút cửa
    return next();
  });

  bot.action(/roll_(.+)/, async (ctx) => {
    const tableId = ctx.match[1];
    const userId = ctx.from.id;
    let db = readDB();
    const table = db.tables[tableId];

    if (!table || table.hostId !== userId) {
      return ctx.answerCbQuery('⚠️ Chỉ có Chủ xị mới có quyền mở bát!', { show_alert: true });
    }

    await executeRoll(bot, tableId, false, ctx);
  });

  async function executeRoll(bot, tableId, isAuto = false, ctx = null) {
    let db = readDB();
    const table = db.tables[tableId];
    if (!table) return;

    table.status = 'finished';
    const hostId = table.hostId;
    const resultDice = table.preResult || ['Bầu', 'Cua', 'Tôm'];
    const counts = {};
    resultDice.forEach(dice => { counts[dice] = (counts[dice] || 0) + 1; });

    let hostNetChange = 0;
    let summaryText = `🎲 **KẾT QUẢ SÓC BẦU CUA ${isAuto ? '(TỰ ĐỘNG)' : ''}**\n\n`;
    summaryText += `🎯 Kết quả: **${resultDice.join(' - ')}**\n\n`;
    summaryText += `📊 **Tổng kết ván chơi:**\n`;

    if (table.bets && Object.keys(table.bets).length > 0) {
      for (const [playerId, userBets] of Object.entries(table.bets)) {
        if (!db.users[playerId]) continue;
        let playerTotalBet = 0, playerTotalPayout = 0;
        for (const [animal, amount] of Object.entries(userBets)) {
          playerTotalBet += amount;
          const matchCount = counts[animal] || 0;
          if (matchCount > 0) {
            playerTotalPayout += amount + (amount * 1.92 * matchCount);
          }
        }
        const playerNetProfit = playerTotalPayout - playerTotalBet;
        db.users[playerId].balance += playerNetProfit;
        hostNetChange -= playerNetProfit;
        summaryText += `- User \`${playerId}\`: ${playerNetProfit >= 0 ? '+' : ''}${Math.round(playerNetProfit).toLocaleString()} điểm\n`;
      }
    } else {
      summaryText += `_Không có ai đặt cược ván này._\n`;
    }

    if (db.users[hostId]) {
      db.users[hostId].balance += hostNetChange;
      summaryText += `\n👑 Chủ xị tổng kết: **${hostNetChange >= 0 ? '+' : ''}${Math.round(hostNetChange).toLocaleString()} điểm**`;
    }

    delete db.tables[tableId];
    writeDB(db);

    const resultKeyboard = Markup.inlineKeyboard([
      [Markup.button.callback('🗑️ Xóa bàn', `close_table_${hostId}`), Markup.button.callback('🎲 Tạo ván mới', 'taoban')]
    ]);

    const mainResultAnimal = resultDice[0];
    const imageName = ANIMAL_IMAGES[mainResultAnimal] || 'bau.jpg';
    const imagePath = path.join(__dirname, '../assets', imageName);

    try {
      if (fs.existsSync(imagePath)) {
        const photoInput = { source: fs.createReadStream(imagePath) };
        if (ctx) {
          await ctx.deleteMessage().catch(() => {});
          await ctx.replyWithPhoto(photoInput, { caption: summaryText, parse_mode: 'Markdown', ...resultKeyboard });
        } else if (table.chatId) {
          await bot.telegram.sendPhoto(table.chatId, photoInput, { caption: summaryText, parse_mode: 'Markdown', ...resultKeyboard });
        }
      } else {
        if (ctx) {
          await ctx.editMessageText(summaryText, { parse_mode: 'Markdown', ...resultKeyboard });
        } else if (table.chatId && table.messageId) {
          await bot.telegram.editMessageText(table.chatId, table.messageId, null, summaryText, { parse_mode: 'Markdown', ...resultKeyboard });
        }
      }
    } catch (err) {
      console.error('Lỗi gửi kết quả:', err.message);
    }
  }

  bot.action(/close_table_(.+)/, (ctx) => {
    ctx.editMessageText(`🚪 **Bàn chơi đã được đóng hoàn toàn.**`, { parse_mode: 'Markdown' });
  });
}

module.exports = { setupGameHandlers };
