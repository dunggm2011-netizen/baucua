from .db import load_data, save_data

# --- XỬ LÝ BÀN CHƠI ---
def tao_ban(cai_id, chat_id):
    data = load_data()
    # Tạo ID bàn mới tự động tăng
    ban_id = str(max([int(k) for k in data["bans"].keys()] + [0]) + 1)
    
    data["bans"][ban_id] = {
        "ban_id": int(ban_id), "cai_id": cai_id, "chat_id": chat_id,
        "trang_thai": "dang_cho", "ket_qua": None, "message_ids": ""
    }
    save_data(data)
    return int(ban_id)

def get_ban(ban_id):
    data = load_data()
    return data["bans"].get(str(ban_id), None)

def get_ban_gan_nhat(chat_id):
    data = load_data()
    bans = [b for b in data["bans"].values() if b["chat_id"] == chat_id]
    return max(bans, key=lambda x: x["ban_id"]) if bans else None

def get_ban_dang_cho(chat_id):
    data = load_data()
    bans = [b for b in data["bans"].values() if b["chat_id"] == chat_id and b["trang_thai"] == "dang_cho"]
    return max(bans, key=lambda x: x["ban_id"]) if bans else None

def cap_nhat_ban(ban_id, **kwargs):
    data = load_data()
    bid = str(ban_id)
    if bid in data["bans"]:
        for key, value in kwargs.items():
            data["bans"][bid][key] = value
        save_data(data)

def khoa_ban(ban_id):
    cap_nhat_ban(ban_id, trang_thai="het_gio")

def ket_thuc_ban(ban_id, ket_qua):
    cap_nhat_ban(ban_id, trang_thai="ket_thuc", ket_qua=ket_qua)

def them_message_id(ban_id, message_id):
    data = load_data()
    bid = str(ban_id)
    if bid in data["bans"]:
        cu = data["bans"][bid]["message_ids"]
        moi = f"{cu},{message_id}" if cu else str(message_id)
        data["bans"][bid]["message_ids"] = moi
        save_data(data)

# --- XỬ LÝ CƯỢC ---
def luu_cuoc(ban_id, user_id, cua, so_diem):
    data = load_data()
    data["cuoc"].append({
        "ban_id": ban_id, "user_id": user_id, "cua": cua, "so_diem": so_diem
    })
    save_data(data)

def get_cuoc_cua_ban(ban_id):
    data = load_data()
    return [c for c in data["cuoc"] if c["ban_id"] == ban_id]

# --- XỬ LÝ GIAO DỊCH NẠP TIỀN ---
def luu_giao_dich(user_id, loai, so_tien, so_diem, ma_don):
    data = load_data()
    data["giao_dich"][ma_don] = {
        "user_id": user_id, "loai": loai, "so_tien": so_tien, 
        "so_diem": so_diem, "ma_don": ma_don, "trang_thai": "cho"
    }
    save_data(data)

def get_giao_dich_by_ma(ma_don):
    data = load_data()
    return data["giao_dich"].get(ma_don, None)

def cap_nhat_giao_dich(ma_don, trang_thai):
    data = load_data()
    if ma_don in data["giao_dich"]:
        data["giao_dich"][ma_don]["trang_thai"] = trang_thai
        save_data(data)
