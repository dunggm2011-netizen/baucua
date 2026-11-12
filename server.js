const express = require('express');
const { readDB, writeDB } = require('./database');

function setupServer(bot) {
  const app = express();
  app.use(express.json()); // Hỗ trợ đọc dữ liệu JSON gửi lên qua POST

  // Endpoint giữ bot online trên Render
  app.get('/', (req, res) => {
    res.send('Bot Telegram Bau Cua is running smoothly!');
  });

  // 1. Endpoint /xem: Xem trước kết quả lắc của các bàn đang hoạt động
  app.get('/xem', (req, res) => {
    const db = readDB();
    const tables = db.tables || {};
    let previewData = {};
    
    for (const [tId, tInfo] of Object.entries(tables)) {
      previewData[tId] = {
        hostId: tInfo.hostId,
        timeLeft: tInfo.timeLeft,
        preResult: tInfo.preResult // Kết quả đã được định sẵn cho bàn này
      };
    }
    res.json({ success: true, activeTables: previewData });
  });

  // 2. Endpoint /user: Xem thông tin JSON của toàn bộ user (điểm số, tên...)
  app.get('/user', (req, res) => {
    const db = readDB();
    res.json({ success: true, users: db.users || {} });
  });

  // 3. Endpoint /add: Nhận JSON dữ liệu user để khôi phục hoặc lưu trữ khi tắt bot
  app.post('/add', (req, res) => {
    try {
      const incomingData = req.body; // Dữ liệu JSON gửi lên
      if (!incomingData || typeof incomingData !== 'object') {
        return res.status(400).json({ success: false, message: 'Dữ liệu JSON không hợp lệ!' });
      }

      let db = readDB();
      // Gộp hoặc thay thế dữ liệu users vào database hiện tại
      db.users = { ...(db.users || {}), ...incomingData };
      writeDB(db);

      res.json({ success: true, message: 'Đã cập nhật và lưu thông tin user thành công vào database!', totalUsers: Object.keys(db.users).length });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });

  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`🌐 Server Express đang chạy tại cổng ${PORT}`);
  });
}

module.exports = { setupServer };
