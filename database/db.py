import sqlite3
import os
from config import DB_PATH

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, ho_ten TEXT, diem INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bans (ban_id INTEGER PRIMARY KEY AUTOINCREMENT, cai_id INTEGER, chat_id INTEGER, trang_thai TEXT DEFAULT 'dang_cho', ket_qua TEXT, message_ids TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cuoc (id INTEGER PRIMARY KEY AUTOINCREMENT, ban_id INTEGER, user_id INTEGER, cua TEXT, so_diem INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS giao_dich (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, loai TEXT, so_tien INTEGER, so_diem INTEGER, ma_don TEXT UNIQUE, trang_thai TEXT DEFAULT 'cho', sepay_id INTEGER UNIQUE)''')
    conn.commit()
    conn.close()
