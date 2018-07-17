from eudplib import *


tbl_ptr, tbl_epd = EUDCreateVariables(2)


def f_init():
    SetVariables([tbl_ptr, tbl_epd], f_dwepdread_epd(EPD(0x6D5A30)))


@EUDFunc
def f_getTblPtr(tblID):
    tbl_offset = f_wread(tbl_ptr + 2 * tblID)
    return tbl_ptr + tbl_offset


def f_setTbl(tblID, *args):
    dst = f_getTblPtr(tblID)
    dst = f_dbstr_print(dst, *args)
