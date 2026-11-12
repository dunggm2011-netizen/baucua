const express = require('express');
const { readDB, writeDB } = require('./database');

function setupServer(bot) {
  const app = express();
  app.use(express.json());
  // Hỗ trợ đọc dữ liệu gửi lên từ form HTML (URL-encoded)
  app.use(express.urlencoded({ extended: true }));

  // Trang chủ
  app.get('/', (req, res) => {
    res.send('Bot Telegram Bau Cua is running smoothly!');
  });

  // API xem bàn chơi
  app.get('/xem', (req, res) => {
    const db = readDB();
    res.json({ success: true, activeTables: db.tables || {} });
  });

  // API xem user
  app.get('/user', (req, res) => {
    const db = readDB();
    res.json({ success: true, users: db.users || {} });
  });

  // GIAO DIỆN HTML CHO ENDPOINT /ADD (Vừa xem vừa paste JSON khôi phục trực tiếp trên web)
  app.get('/add', (req, res) => {
    res.send(`
      <!DOCTYPE html>
      <html lang="vi">
      <head>
          <meta charset="UTF-8">
          <title>Khôi phục Dữ liệu Bot Bầu Cua</title>
          <style>
              body { font-family: Arial, sans-serif; background: #121212; color: #fff; padding: 20px; }
              .container { max-width: 600px; margin: 0 auto; background: #1e1e1e; padding: 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
              h2 { color: #4CAF50; text-align: center; }
              textarea { width: 100%; height: 250px; background: #2d2d2d; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 10px; font-family: monospace; font-size: 14px; }
              button { background: #4CAF50; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 4px; cursor: pointer; width: 100%; margin-top: 15px; }
              button:hover { background: #45a049; }
              #result { margin-top: 15px; padding: 10px; border-radius: 4px; text-align: center; font-weight: bold; }
          </style>
      </head>
      <body>
          <div class="container">
              <h2>🛠️ Khôi phục / Cập nhật User JSON</h2>
              <p>Dán đoạn JSON dữ liệu user vào ô bên dưới rồi bấm nút khôi phục:</p>
              <textarea id="jsonInput" placeholder='{"123456": {"balance": 500000}}'></textarea>
              <button onclick="submitData()">Khôi phục Dữ liệu Ngay</button>
              <div id="result"></div>
          </div>

          <script>
              async function submitData() {
                  const rawData = document.getElementById('jsonInput').value;
                  const resultDiv = document.getElementById('result');
                  
                  try {
                      const parsedJson = JSON.parse(rawData);
                      const response = await fetch('/add', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify(parsedJson)
                      });
                      const data = await response.json();
                      if (data.success) {
                          resultDiv.style.color = '#4CAF50';
                          resultDiv.innerText = '✅ ' + data.message + ' (Tổng số user: ' + data.totalUsers + ')';
                      } else {
                          resultDiv.style.color = '#ff5252';
                          resultDiv.innerText = '❌ Lỗi: ' + data.message;
                      }
                  } catch (e) {
                      resultDiv.style.color = '#ff5252';
                      resultDiv.innerText = '❌ Định dạng JSON không hợp lệ! Hãy kiểm tra lại dấu ngoặc.';
                  }
              }
          </script>
      </body>
      </html>
    `);
  });

  // Xử lý POST /add khi bấm nút từ giao diện web hoặc tool gửi lên
  app.post('/add', (req, res) => {
    try {
      const incomingData = req.body;
      if (!incomingData || typeof incomingData !== 'object' || Object.keys(incomingData).length === 0) {
        return res.status(400).json({ success: false, message: 'Dữ liệu JSON trống hoặc không hợp lệ!' });
      }

      let db = readDB();
      db.users = { ...(db.users || {}), ...incomingData };
      writeDB(db);

      res.json({ 
        success: true, 
        message: 'Khôi phục dữ liệu thành công!', 
        totalUsers: Object.keys(db.users).length 
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  });

  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`🌐 Server Express đang chạy tại cổng ${PORT}`);
  });
}

module.exports = { setupServer };
