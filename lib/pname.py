from eudplib import *
import customText4 as ct
from eudplib.eudlib.stringf.rwcommon import br1, br2

baselen = EUDArray(8)


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


def _init():
    if EUDPlayerLoop()():
        playerid = 0x57EEEB + 36 * f_getcurpl()
        baselen[f_getcurpl()] = f_strlen(playerid)
    EUDEndPlayerLoop()


EUDOnStart(_init)


def SetName(player, *name):
    if not isUnproxyInstance(player, int):
        player = EncodePlayer(player)
    temp = Db(218)
    bname, blen = 0x57EEEB + 36 * player, baselen[player]
    _end = Forward()
    EUDJumpIf(f_playerexist(player) == 0, _end)
    for line in EUDLoopRange(11):
        L = 0x640B60 + 218 * line
        if EUDIf()(f_memcmp(bname, L, blen) == 0):
            f_dbstr_addstr(temp, L + blen)
            ct.f_sprintf(L, *(name + (ct.f_str(temp),)))
        EUDEndIf()
    _end << NextTrigger()
