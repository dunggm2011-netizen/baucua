from .db import load_data, save_data

def get_user(user_id):
    data = load_data()
    return data["users"].get(str(user_id), None)

def create_user(user_id, username, ho_ten):
    data = load_data()
    uid = str(user_id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "user_id": user_id, "username": username, "ho_ten": ho_ten, 
            "diem": 0, "tong_nap": 0, "da_cuoc": 0
        }
        save_data(data)

def get_diem(user_id):
    user = get_user(user_id)
    return user['diem'] if user else 0

def cong_diem(user_id, so_diem):
    data = load_data()
    uid = str(user_id)
    if uid in data["users"]:
        data["users"][uid]['diem'] += so_diem
        save_data(data)

def tru_diem(user_id, so_diem):
    data = load_data()
    uid = str(user_id)
    if uid in data["users"] and data["users"][uid]['diem'] >= so_diem:
        data["users"][uid]['diem'] -= so_diem
        save_data(data)
        return True
    return False

def cong_tien_cuoc(user_id, so_diem_cuoc):
    data = load_data()
    uid = str(user_id)
    if uid in data["users"]:
        data["users"][uid]['da_cuoc'] += so_diem_cuoc
        save_data(data)

def cong_tien_nap(user_id, so_diem_nap):
    data = load_data()
    uid = str(user_id)
    if uid in data["users"]:
        data["users"][uid]['tong_nap'] += so_diem_nap
        save_data(data)

def get_tien_cuoc_va_nap(user_id):
    user = get_user(user_id)
    if user:
        return {"tong_nap": user.get('tong_nap', 0), "da_cuoc": user.get('da_cuoc', 0)}
    return {"tong_nap": 0, "da_cuoc": 0}
