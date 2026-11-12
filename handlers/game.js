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

const userBetStates = {};
const BET_STATE_TIMEOUT = 60 * 1000;

function setupGameHandlers(bot) {
  // 1. TẠO BÀN
  bot.action('taoban', async (ctx) => {
    const userId = ctx.from.id;
    let db = readDB();
    const userBalance = db.users[userId]?.balance || 0;

    if (userBalance < 100000) {
      return ctx.answerCbQuery('⚠️ Bạn cần tối thiểu 100.000 điểm để làm cái!', { show_alert: true });
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
      timeLeft: 50,
      chatId: ctx.chat.id
    };
    writeDB(db);

    const sentMsg = await ctx.editMessageText(buildTableText(tableId, db.tables[tableId]), {
      parse_mode: 'Markdown',
      ...getTableKeyboard(tableId)
    });

    db = readDB();
    if (db.tables[tableId]) {
      db.tables[tableId].messageId = sentMsg.message_id;
      writeDB(db);
    }

    startCountdown(bot, tableId);
  });

  function buildTableText(tableId, table) {
    let betSummary = "";
    if (table.bets) {
      const totals = {};
      for (const pId in table.bets) {
        for (const anim in table.bets[pId]) {
          totals[anim] = (totals[anim] || 0) + table.bets[pId][anim];
        }
      }
      if (Object.keys(totals).length > 0) {
        betSummary = "\n📋 **Tổng cược hiện tại:**\n";
        for (const [anim, amt] of Object.entries(totals)) {
          betSummary += `• ${anim}: ${amt.toLocaleString()}đ\n`;
        }
        betSummary += "\n";
      }
    }

    return `🎲 **BÀN BẦU CUA ĐANG MỞ CƯỢC**\n` +
           `👑 Chủ xị: \`${table.hostId}\`\n` +
           `⏳ **Thời gian còn lại: ${table.timeLeft} giây**\n` +
           betSummary +
           `_Luật: Min cược 100 - Max 100.000 điểm_\n👉 Chọn cửa cược bên dưới:`;
  }

  function getTableKeyboard(tableId) {
    return Markup.inlineKeyboard([
      [Markup.button.callback('🦌 Nai', `bet_${tableId}_Nai`), Markup.button.callback(' Bầu', `bet_${tableId}_Bầu`), Markup.button.callback('🐔 Gà', `bet_${tableId}_Gà`)],
      [Markup.button.callback('🐟 Cá', `bet_${tableId}_Cá`), Markup.button.callback('🦀 Cua', `bet_${tableId}_Cua`), Markup.button.callback('🦐 Tôm', `bet_${tableId}_Tôm`)]
    ]);
  }

  function getWaitingRollKeyboard(tableId) {
    return Markup.inlineKeyboard([
      [Markup.button.callback('🎲 SÓC BẦU CUA', `roll_${tableId}`)]
    ]);
  }

  // 2. ĐẾM NGƯỢC
  function startCountdown(bot, tableId) {
    const timer = setInterval(async () => {
      try {
        let db = readDB();
        const table = db.tables[tableId];

        if (!table || table.status !== 'betting') {
          clearInterval(timer);
          return;
        }

        if (table.timeLeft <= 1) {
          clearInterval(timer);
          table.timeLeft = 0;
          table.status = 'waiting_roll'; 
          writeDB(db);

          try {
            await bot.telegram.editMessageText(
              table.chatId, table.messageId, null,
              `⏰ **ĐÃ HẾT THỜI GIAN CƯỢC**\n\n👑 Chủ xị \`${table.hostId}\` hãy bấm nút bên dưới để sóc bầu cua!`,
              { parse_mode: 'Markdown', ...getWaitingRollKeyboard(tableId) }
            );
          } catch (e) {}
          return;
        }

        table.timeLeft -= 1;
        writeDB(db);

        try {
          await bot.telegram.editMessageText(
            table.chatId, table.messageId, null,
            buildTableText(tableId, table),
            { parse_mode: 'Markdown', ...getTableKeyboard(tableId) }
          );
        } catch (e) {}
      } catch (err) {
        console.error('Lỗi ở bộ đếm ngược:', err.message);
      }
    }, 1000);
  }

  // 3. NÚT SÓC (Dành cho chủ xị)
  bot.action(/roll_(.+)/, async (ctx) => {
    try { await ctx.answerCbQuery('🎲 Đang sóc...'); } catch (e) {}

    try {
      const tableId = ctx.match[1];
      const userId = ctx.from.id;

      let db = readDB();
      const table = db.tables[tableId];

      if (!table || table.status !== 'waiting_roll') {
        return ctx.reply('⚠️ Ván này đã được sóc hoặc không tồn tại!');
      }

      if (String(table.hostId) !== String(userId)) {
        return ctx.reply('⚠️ Chỉ chủ xị mới được bấm nút sóc!');
      }

      table.status = 'rolling';
      writeDB(db);
      
      await executeRoll(bot, tableId, false);
      
    } catch (err) {
      console.error('❌ LỖI Ở NÚT SÓC:', err.message);
    }
  });

  // 4. ĐẶT CƯỢC
  bot.action(/bet_(.+)_(.+)/, (ctx) => {
    const tableId = ctx.match[1];
    const choice = ctx.match[2];
    let db = readDB();

    if (!db.tables[tableId] || db.tables[tableId].status !== 'betting') {
      return ctx.answerCbQuery('⚠️ Bàn chơi đã hết thời gian cược hoặc không tồn tại!', { show_alert: true });
    }

    const userId = ctx.from.id.toString();

    if (userBetStates[userId]?.timeoutId) {
      clearTimeout(userBetStates[userId].timeoutId);
    }

    const timeoutId = setTimeout(() => {
      if (userBetStates[userId]) delete userBetStates[userId];
    }, BET_STATE_TIMEOUT);

    userBetStates[userId] = { tableId, choice, timeoutId };

    ctx.answerCbQuery(`Đã chọn cửa [${choice}]. Gửi số điểm cược vào khung chat (ví dụ: 1000):`);
  });

  bot.on('text', async (ctx, next) => {
    const userId = ctx.from.id.toString();
    if (!userBetStates[userId]) return next();

    const text = ctx.message.text.trim();
    const amount = Number(text);

    if (!Number.isInteger(amount) || amount <= 0) {
      if (userBetStates[userId]?.timeoutId) clearTimeout(userBetStates[userId].timeoutId);
      delete userBetStates[userId];
      return ctx.reply('⚠️ Số tiền cược không hợp lệ. Vui lòng bấm lại nút con vật để cược!');
    }

    const { tableId, choice, timeoutId } = userBetStates[userId];
    if (timeoutId) clearTimeout(timeoutId);
    delete userBetStates[userId];

    let db = readDB();
    const table = db.tables[tableId];
    
    if (!table || table.status !== 'betting') {
      return ctx.reply('⚠️ Bàn chơi đã hết thời gian cược!');
    }

    if (!db.users[userId]) db.users[userId] = { balance: 0 };
    if (isNaN(db.users[userId].balance)) db.users[userId].balance = 0;

    if (db.users[userId].balance < amount) {
      return ctx.reply(`⚠️ Số dư của bạn không đủ ${amount.toLocaleString()} điểm để cược!`);
    }

    if (amount < 100 || amount > 100000) {
      return ctx.reply('⚠️ Mức cược phải từ 100 đến 100.000 điểm!');
    }

    db.users[userId].balance -= amount;

    if (!table.bets[userId]) table.bets[userId] = {};
    table.bets[userId][choice] = (table.bets[userId][choice] || 0) + amount;

    writeDB(db);

    await ctx.reply(`✅ Đã đặt cược thành công **${amount.toLocaleString()} điểm** vào cửa **${choice}**!`, { parse_mode: 'Markdown' });

    try {
      await bot.telegram.editMessageText(
        table.chatId, table.messageId, null,
        buildTableText(tableId, table),
        { parse_mode: 'Markdown', ...getTableKeyboard(tableId) }
      );
    } catch (e) {}
  });

  // 5. MỞ BÁT VÀ TRẢ THƯỞNG
  async function executeRoll(bot, tableId, isAuto = false) {
    try {
      let db = readDB();
      const table = db.tables[tableId];
      if (!table) return;

      const hostId = table.hostId;
      const resultDice = table.preResult || ['Bầu', 'Cua', 'Tôm'];
      const counts = {};
      resultDice.forEach(dice => { counts[dice] = (counts[dice] || 0) + 1; });

      let hostNetChange = 0;
      let summaryText = `🎲 **KẾT QUẢ SÓC BẦU CUA**\n\n`;
      summaryText += `🎯 Kết quả: **${resultDice.join(' - ')}**\n\n`;
      summaryText += `📊 **Tổng kết ván chơi:**\n`;

      if (table.bets && Object.keys(table.bets).length > 0) {
        for (const [playerId, userBets] of Object.entries(table.bets)) {
          if (!db.users[playerId]) db.users[playerId] = { balance: 0 };
          if (isNaN(db.users[playerId].balance)) db.users[playerId].balance = 0;

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
          if (isNaN(db.users[playerId].balance)) db.users[playerId].balance = 0;
          
          hostNetChange -= playerNetProfit;
          summaryText += `- User \`${playerId}\`: ${playerNetProfit >= 0 ? '+' : ''}${Math.round(playerNetProfit).toLocaleString()} điểm\n`;
        }
      } else {
        summaryText += `_Không có ai đặt cược ván này._\n`;
      }

      if (db.users[hostId]) {
        if (isNaN(db.users[hostId].balance)) db.users[hostId].balance = 0;
        db.users[hostId].balance += hostNetChange;
        if (isNaN(db.users[hostId].balance)) db.users[hostId].balance = 0;
        summaryText += `\n👑 Chủ xị tổng kết: **${hostNetChange >= 0 ? '+' : ''}${Math.round(hostNetChange).toLocaleString()} điểm**`;
      }

      // Xoá bàn khỏi database
      delete db.tables[tableId];
      writeDB(db);

      const resultKeyboard = Markup.inlineKeyboard([
        [Markup.button.callback('🔄 Ván Tiếp Theo', `nextgame_${hostId}`)],
        [Markup.button.callback('🗑️ Xóa bàn', `close_table_${hostId}`)]
      ]);

      // Hiển thị kết quả dạng TEXT trước để không bị xoay loading
      try {
        await bot.telegram.editMessageText(
          table.chatId, table.messageId, null,
          summaryText,
          { parse_mode: 'Markdown', ...resultKeyboard }
        );
      } catch (e) {
        await bot.telegram.sendMessage(table.chatId, summaryText, { parse_mode: 'Markdown', ...resultKeyboard }).catch(() => {});
      }

      // Gửi ảnh con vật dưới dạng tin nhắn mới
      const mainResultAnimal = resultDice[0];
      const imageName = ANIMAL_IMAGES[mainResultAnimal] || 'bau.jpg';
      const imagePath = path.join(__dirname, '../assets', imageName);

      if (fs.existsSync(imagePath) && table.chatId) {
        try {
          await bot.telegram.sendPhoto(
            table.chatId,
            { source: fs.createReadStream(imagePath) },
            { caption: `🎯 **${mainResultAnimal.toUpperCase()}**`, parse_mode: 'Markdown' }
          );
        } catch (err) {
          console.error('❌ LỖI GỬI ẢNH:', err.message);
        }
      }

    } catch (err) {
      console.error('Lỗi khi thực hiện mở bát:', err.message);
    }
  }

  // 6. NÚT VÁN TIẾP THEO
  bot.action(/nextgame_(.+)/, async (ctx) => {
    try { await ctx.answerCbQuery('🔄 Đang tạo ván mới...'); } catch (e) {}

    const hostId = ctx.match[1];
    const userId = ctx.from.id;

    if (String(hostId) !== String(userId)) {
      return ctx.reply('⚠️ Chỉ chủ xị mới có quyền tạo ván tiếp theo!');
    }

    let db = readDB();
    const userBalance = db.users[userId]?.balance || 0;

    if (userBalance < 100000) {
      return ctx.reply('⚠️ Bạn cần tối thiểu 100.000 điểm để tiếp tục làm cái!');
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
      timeLeft: 50,
      chatId: ctx.chat.id
    };
    writeDB(db);

    const sentMsg = await ctx.editMessageText(buildTableText(tableId, db.tables[tableId]), {
      parse_mode: 'Markdown',
      ...getTableKeyboard(tableId)
    });

    db = readDB();
    if (db.tables[tableId]) {
      db.tables[tableId].messageId = sentMsg.message_id;
      writeDB(db);
    }

    startCountdown(bot, tableId);
  });

  // 7. NÚT XOÁ BÀN
  bot.action(/close_table_(.+)/, (ctx) => {
    ctx.editMessageText(`🚪 **Bàn chơi đã được đóng hoàn toàn.**`, { parse_mode: 'Markdown' });
  });
}

module.exports = { setupGameHandlers };
