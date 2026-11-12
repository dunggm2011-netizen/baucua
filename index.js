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

// ==================== 1. KÍCH HOẠT TẤT CẢ HANDLERS & SERVER ====================
try {
  setupMenuHandlers(bot);
  setupGameHandlers(bot);
  setupWithdrawHandlers(bot);
  setupDepositHandlers(bot);
  setupAdminHandlers(bot);
  setupGiftcodeHandlers(bot);
  console.log('✅ Đã nạp tất cả Telegram Handlers thành công!');

  // Kích hoạt Web Server (giao diện quản lý /add, /xem,...)
  setupServer(bot);
  console.log('✅ Đã khởi chạy Web Server thành công!');
} catch (error) {
  console.error('❌ Lỗi khi khởi tạo handlers hoặc server:', error.message);
}

// ==================== 2. VÒNG LẶP TỰ ĐỘNG QUÉT NẠP TIỀN ====================
// Cứ mỗi 5 giây, gọi API ngân hàng qua bankService để tự động quét nội dung NAP và cộng điểm
setInterval(() => {
  checkBankTransactions(bot);
}, 5000);

// ==================== 3. KHỞI ĐỘNG BOT TELEGRAM ====================
bot.launch().then(() => {
  console.log('🚀 Bot Telegram Bầu Cua & Hệ thống Nạp Tự Động đã sẵn sàng hoạt động!');
}).catch((err) => {
  console.error('❌ Lỗi khởi động bot:', err);
});

// Xử lý ngắt tiến trình an toàn
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
