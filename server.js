const express = require('express');

function setupServer() {
  const app = express();
  app.use(express.json());

  app.get('/', (req, res) => {
    res.send('Telegram Bot Bầu Cua is running smoothly!');
  });

  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Server HTTP đang chạy trên cổng ${PORT}`);
  });
}

module.exports = { setupServer };
