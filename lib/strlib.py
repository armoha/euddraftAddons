from eudplib import *
from eudplib.eudlib.stringf.rwcommon import br1, br2


@EUDFunc
def f_memcmp(str1, str2, count):
    c = EUDVariable()
    c << count
    br1.seekoffset(str1)
    br2.seekoffset(str2)

    if EUDWhile()(c.AtLeast(1)):
        c -= 1
        ch1 = br1.readbyte()
        ch2 = br2.readbyte()
        if EUDIf()(ch1 == ch2):
            EUDContinue()
        EUDEndIf()
        EUDReturn(ch1 - ch2)
    EUDEndWhile()

    EUDReturn(0)


@EUDFunc
def f_strlen(src):
    ret = EUDVariable()
    ret << 0
    br1.seekoffset(src)
    if EUDWhile()(br1.readbyte() >= 1):
        ret += 1
    EUDEndWhile()
    EUDReturn(ret)


@EUDFunc
def f_strnstr(string, substring, count):
    # O(mn)
    br1.seekoffset(string)
    br2.seekoffset(substring)
    dst = EUDVariable()
    dst << -1

    b = br2.readbyte()
    if EUDIf()(b == 0):
        EUDReturn(string)
    EUDEndIf()
    if EUDWhile()(count >= 1):
        a = br1.readbyte()
        dst += 1
        count -= 1
        if EUDIf()(EUDSCOr()(a == 0)()):
            EUDBreak()
        if EUDElseIfNot()(a == b):
            EUDContinue()
        EUDEndIf()
        br1_epdoffset = br1._offset
        br1_suboffset = br1._suboffset
        if EUDWhile()(1):
            c = br2.readbyte()
            if EUDIf()(c == 0):
                EUDReturn(string + dst)
            if EUDElseIfNot()(br1.readbyte() == c):
                EUDBreak()
            EUDEndIf()
        EUDEndWhile()
        br1.seekepd(br1_epdoffset)
        br1._suboffset = br1_suboffset
        br2.seekoffset(substring + 1)
    EUDEndWhile()
    EUDReturn(-1)
