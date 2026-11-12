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
  return JSON.parse(fs.readFileSync(DB_PATH, 'utf8'));
}

function writeDB(data) {
  fs.writeFileSync(DB_PATH, JSON.stringify(data, null, 2));
}

module.exports = { readDB, writeDB };
