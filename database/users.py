from .db import get_conn

def get_user(user_id):
    conn = get_conn()
    # Dùng %s cho Postgres
    row = conn.execute('SELECT * FROM users WHERE user_id=%s', (user_id,)).fetchone()
    conn.close()
    return row

def create_user(user_id, username, ho_ten):
    conn = get_conn()
    # ON CONFLICT DO NOTHING tương đương với INSERT OR IGNORE của SQLite
    conn.execute('INSERT INTO users (user_id, username, ho_ten) VALUES (%s,%s,%s) ON CONFLICT (user_id) DO NOTHING', (user_id, username, ho_ten))
    conn.commit()
    conn.close()

def get_diem(user_id):
    row = get_user(user_id)
    return row['diem'] if row else 0

def cong_diem(user_id, so_diem):
    conn = get_conn()
    conn.execute('UPDATE users SET diem = diem + %s WHERE user_id=%s', (so_diem, user_id))
    conn.commit()
    conn.close()

def tru_diem(user_id, so_diem):
    conn = get_conn()
    row = conn.execute('SELECT diem FROM users WHERE user_id=%s', (user_id,)).fetchone()
    
    if not row or row['diem'] < so_diem:
        conn.close()
        return False
        
    conn.execute('UPDATE users SET diem = diem - %s WHERE user_id=%s', (so_diem, user_id))
    conn.commit()
    conn.close()
    return True

def cong_tien_cuoc(user_id, so_diem_cuoc):
    conn = get_conn()
    conn.execute('UPDATE users SET da_cuoc = da_cuoc + %s WHERE user_id=%s', (so_diem_cuoc, user_id))
    conn.commit()
    conn.close()

def cong_tien_nap(user_id, so_diem_nap):
    conn = get_conn()
    conn.execute('UPDATE users SET tong_nap = tong_nap + %s WHERE user_id=%s', (so_diem_nap, user_id))
    conn.commit()
    conn.close()

def get_tien_cuoc_va_nap(user_id):
    conn = get_conn()
    row = conn.execute('SELECT tong_nap, da_cuoc FROM users WHERE user_id=%s', (user_id,)).fetchone()
    conn.close()
    return row if row else {'tong_nap': 0, 'da_cuoc': 0}
