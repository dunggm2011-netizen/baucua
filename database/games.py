from .db import get_conn

def luu_giao_dich(user_id, so_tien, so_diem, ma_don):
    conn = get_conn()
    conn.execute('INSERT INTO giao_dich (user_id, so_tien, so_diem, ma_don) VALUES (?,?,?,?)', (user_id, so_tien, so_diem, ma_don))
    conn.commit()
    conn.close()

def get_giao_dich_by_ma(ma_don):
    conn = get_conn()
    row = conn.execute('SELECT * FROM giao_dich WHERE ma_don=?', (ma_don,)).fetchone()
    conn.close()
    return row

def cap_nhat_giao_dich(ma_don, trang_thai):
    conn = get_conn()
    conn.execute('UPDATE giao_dich SET trang_thai=? WHERE ma_don=?', (trang_thai, ma_don))
    conn.commit()
    conn.close()
