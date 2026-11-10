def tinh_thang_thua(cua_dat, so_diem_dat, ket_qua):
    so_lan = ket_qua.count(cua_dat)
    if so_lan == 0:
        return False, 0
    return True, so_diem_dat * so_lan
