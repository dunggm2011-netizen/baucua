const { Telegraf } = require('telegraf');
const config = require('./config');
const { setupServer } = require('./server');
const { checkBankTransactions } = require('./services/bankService');
const { setupMenuHandlers } = require('./handlers/menu');
const { setupGameHandlers } = require('./handlers/game');
const { setupWithdrawHandlers } = require('./handlers/withdraw');
const { setupDepositHandlers } = require('./handlers/deposit');
const { setupAdminHandlers } = require('./handlers/admin');
const { setupGiftcodeHandlers } = require('./handlers/giftcode');

const bot = new Telegraf(config.BOT_TOKEN);

// Khởi động Express Server cho Render
setupServer();

// Đăng ký toàn bộ Handler
setupMenuHandlers(bot);
setupGameHandlers(bot);
setupWithdrawHandlers(bot);
setupDepositHandlers(bot);
setupAdminHandlers(bot);
setupGiftcodeHandlers(bot);

// Vòng lặp quét API ngân hàng mỗi 15 giây
setInterval(() => checkBankTransactions(bot), 15000);

// Khởi chạy Bot
bot.launch().then(() => {
  console.log('🤖 Bot Telegram Bầu Cua đã khởi động thành công!');
});

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
