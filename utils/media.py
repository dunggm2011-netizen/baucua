import os
import random
from config import CON_VAT, IMG_DIR

def random_ket_qua():
    return [random.choice(CON_VAT) for _ in range(3)]

def get_anh(con_vat):
    path = os.path.join(IMG_DIR, f'{con_vat}.jpg')
    return path if os.path.exists(path) else None
