from .db import get_conn

def get_user(user_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM users WHERE user_id=?', (user_id,)).fetchone()
    conn.close()
    return row

def create_user(user_id, username, ho_ten):
    conn = get_conn()
    conn.execute('INSERT OR IGNORE INTO users (user_id, username, ho_ten) VALUES (?,?,?)', (user_id, username, ho_ten))
    conn.commit()
    conn.close()

def get_diem(user_id):
    row = get_user(user_id)
    return row['diem'] if row else 0

def cong_diem(user_id, so_diem):
    conn = get_conn()
    conn.execute('UPDATE users SET diem = diem + ? WHERE user_id=?', (so_diem, user_id))
    conn.commit()
    conn.close()

def tru_diem(user_id, so_diem):
    conn = get_conn()
    row = conn.execute('SELECT diem FROM users WHERE user_id=?', (user_id,)).fetchone()
    if not row or row['diem'] < so_diem:
        conn.close()
        return False
    conn.execute('UPDATE users SET diem = diem - ? WHERE user_id=?', (so_diem, user_id))
    conn.commit()
    conn.close()
    return True
