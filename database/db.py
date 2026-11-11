import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_conn():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.DictCursor 
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect('game_data.db')
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY, 
        username TEXT, 
        ho_ten TEXT, 
        diem INTEGER DEFAULT 0,
        tong_nap INTEGER DEFAULT 0,
        da_cuoc INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bans (
        ban_id SERIAL PRIMARY KEY, 
        cai_id BIGINT, 
        chat_id BIGINT, 
        trang_thai TEXT DEFAULT 'dang_cho', 
        ket_qua TEXT, 
        message_ids TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS cuoc (
        id SERIAL PRIMARY KEY, 
        ban_id INTEGER, 
        user_id BIGINT, 
        cua TEXT, 
        so_diem INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS giao_dich (
        id SERIAL PRIMARY KEY, 
        user_id BIGINT, 
        loai TEXT, 
        so_tien INTEGER, 
        so_diem INTEGER, 
        ma_don TEXT UNIQUE, 
        trang_thai TEXT DEFAULT 'cho'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS yeu_cau_rut (
        id SERIAL PRIMARY KEY, 
        user_id BIGINT, 
        so_diem INTEGER, 
        stk TEXT, 
        ten_chu_the TEXT,
        trang_thai TEXT DEFAULT 'cho_duyet'
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Kết nối và tạo bảng trên Neon (PostgreSQL) thành công!")
