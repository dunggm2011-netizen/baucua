import json
import os
import threading

DATA_FILE = "data.json"
lock = threading.Lock() # Chống ghi đè dữ liệu khi nhiều người thao tác cùng lúc

def load_data():
    if not os.path.exists(DATA_FILE):
        # Nếu chưa có file, tạo cấu trúc rỗng
        data = {"users": {}, "bans": {}, "cuoc": [], "giao_dich": {}, "yeu_cau_rut": {}}
        save_data(data)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

def init_db():
    # Chỉ cần gọi hàm load_data để đảm bảo file tồn tại
    load_data()
    print("✅ Hệ thống file data.json đã sẵn sàng.")
