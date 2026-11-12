const fs = require('fs');
const path = require('path');

const DB_PATH = path.join(__dirname, 'database.json');

function initDB() {
  if (!fs.existsSync(DB_PATH)) {
    const initialData = { 
      users: {},   
      tables: {},
      banned: [],
      giftcodes: {},
      processedTxs: []
    };
    fs.writeFileSync(DB_PATH, JSON.stringify(initialData, null, 2));
  }
}

function readDB() {
  initDB();
  try {
    const data = fs.readFileSync(DB_PATH, 'utf8');
    const parsed = JSON.parse(data);
    
    // Đảm bảo các key cơ bản luôn tồn tại để không bị lỗi undefined
    if (!parsed.users) parsed.users = {};
    if (!parsed.tables) parsed.tables = {};
    if (!parsed.banned) parsed.banned = [];
    if (!parsed.giftcodes) parsed.giftcodes = {};
    if (!parsed.processedTxs) parsed.processedTxs = [];
    
    return parsed;
  } catch (err) {
    console.error('❌ LỖI ĐỌC FILE DATABASE.JSON:', err.message);
    return { users: {}, tables: {}, banned: [], giftcodes: {}, processedTxs: [] };
  }
}

function writeDB(data) {
  try {
    fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
  } catch (err) {
    console.error('❌ LỖI GHI FILE DATABASE.JSON:', err.message);
  }
}

module.exports = { readDB, writeDB };
