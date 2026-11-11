from .db import get_conn

# --- XỬ LÝ BÀN CHƠI ---
def tao_ban(cai_id, chat_id):
    conn = get_conn()
    cur = conn.execute('INSERT INTO bans (cai_id, chat_id) VALUES (?,?)', (cai_id, chat_id))
    ban_id = cur.lastrowid
    conn.commit()
    conn.close()
    return ban_id

def get_ban(ban_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM bans WHERE ban_id=?', (ban_id,)).fetchone()
    conn.close()
    return row

def get_ban_gan_nhat(chat_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM bans WHERE chat_id=? ORDER BY ban_id DESC LIMIT 1", (chat_id,)).fetchone()
    conn.close()
    return row

def get_ban_dang_cho(chat_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM bans WHERE chat_id=? AND trang_thai='dang_cho' ORDER BY ban_id DESC LIMIT 1", (chat_id,)).fetchone()
    conn.close()
    return row

def khoa_ban(ban_id):
    conn = get_conn()
    conn.execute("UPDATE bans SET trang_thai='het_gio' WHERE ban_id=?", (ban_id,))
    conn.commit()
    conn.close()

def ket_thuc_ban(ban_id, ket_qua):
    conn = get_conn()
    conn.execute("UPDATE bans SET trang_thai='ket_thuc', ket_qua=? WHERE ban_id=?", (ket_qua, ban_id))
    conn.commit()
    conn.close()

def them_message_id(ban_id, message_id):
    conn = get_conn()
    row = conn.execute("SELECT message_ids FROM bans WHERE ban_id=?", (ban_id,)).fetchone()
    cu = row['message_ids'] if row and row['message_ids'] else ""
    moi = f"{cu},{message_id}" if cu else str(message_id)
    conn.execute("UPDATE bans SET message_ids=? WHERE ban_id=?", (moi, ban_id))
    conn.commit()
    conn.close()

# --- XỬ LÝ CƯỢC ---
def luu_cuoc(ban_id, user_id, cua, so_diem):
    conn = get_conn()
    conn.execute('INSERT INTO cuoc (ban_id, user_id, cua, so_diem) VALUES (?,?,?,?)', (ban_id, user_id, cua, so_diem))
    conn.commit()
    conn.close()

def get_cuoc_cua_ban(ban_id):
    conn = get_conn()
    rows = conn.execute('SELECT * FROM cuoc WHERE ban_id=?', (ban_id,)).fetchall()
    conn.close()
    return rows

# --- XỬ LÝ GIAO DỊCH NẠP TIỀN ---
def luu_giao_dich(user_id, loai, so_tien, so_diem, ma_don):
    conn = get_conn()
    conn.execute('''INSERT INTO giao_dich (user_id, loai, so_tien, so_diem, ma_don) VALUES (?,?,?,?,?)''', (user_id, loai, so_tien, so_diem, ma_don))
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
