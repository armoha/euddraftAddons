# -*- coding: utf-8 -*-
import math

import eudplib.eudlib.stringf.cputf8 as cputf
from eudplib import *
from eudplib.eudlib.stringf.rwcommon import br1, bw1


"""
customText 0.2.1

0.2.2
0.2.1 f_playSoundP, f_playSoundAll work properly.
0.2.0 Add Legacy Support: chatAnnouncement + old function names.
    Add f_chatprintAll/_epd. Change f_chatprint: print for CurrentPlayer.
    Add f_get(EUDVariable): retrieve current position.
0.1.3 f_add1c_epd makes malaligned string when it doesn't have a color code
0.1.2 fix EUD error when modify stat_txt.tbl
0.1.1 fix bug; ct.epd/ptr set to 0 in SC 1.16
0.1.0 initial release
"""


def f_b2i(x):
    return int.from_bytes(x, byteorder='little')


def _CGFW(exprf, retn):
    rets = [ExprProxy(None) for _ in range(retn)]

    def _():
        vals = exprf()
        for ret, val in zip(rets, vals):
            ret._value = val
    EUDOnStart(_)
    return rets


legacySupport = 0
setoldcp, setlocalcp = Forward(), Forward()
ptr, epd, cp, nmod = EUDCreateVariables(4)
player_colors = "\x08\x0E\x0F\x10\x11\x15\x16\x17\x18\x19\x1B\x1C\x1D\x1E\x1F"
Color = EUDArray([Db(u2b(x)) for x in player_colors])
strBuffer = _CGFW(lambda: [GetStringIndex("i" * 1308)], 1)[0]
STR_ptr, STR_epd = EUDCreateVariables(2)
AddSTR_ptr, AddSTR_epd, write_ptr, write_epd = [Forward() for i in range(4)]
chatptr, chatepd = EUDCreateVariables(2)


@EUDFunc
def f_getoldcp():
    DoActions(SetMemory(setoldcp + 20, SetTo, 0))
    for i in range(31, -1, -1):
        RawTrigger(
            conditions=[
                Memory(0x6509B0, AtLeast, 2**i)
            ],
            actions=[
                SetMemory(0x6509B0, Subtract, 2**i),
                SetMemory(setoldcp + 20, Add, 2**i)
            ]
        )


@EUDFunc
def f_setoldcp():
    DoActions(setoldcp << SetMemory(0x6509B0, SetTo, 0))


@EUDFunc
def f_setlocalcp():
    DoActions(setlocalcp << SetMemory(0x6509B0, SetTo, 0))


def f_is116():
    return Memory(0x51CE84, AtMost, 99)


def f_cp949_to_utf8_copy(dst, src, flag='ptr'):
    br1.seekoffset(src)
    if flag == 'ptr':
        bw1.seekoffset(dst)

    if EUDInfLoop()():
        b1 = br1.readbyte()
        EUDBreakIf(b1 == 0)
        if EUDIf()(b1 < 128):
            if flag == 'ptr':
                bw1.writebyte(b1)
                dst += 1
            elif flag == 'epd':
                f_dwwrite_epd(dst, b1 + 0xD0D0D00)
        if EUDElse()():
            b2 = br1.readbyte()
            EUDBreakIf(b2 == 0)
            code = cputf.cvtb[b2 * 256 + b1]
            if EUDIf()(code <= 0x07FF):  # Encode as 2-byte
                if flag == 'ptr':
                    bw1.writebyte(0b11000000 | (code // (1 << 6)) & 0b11111)
                    bw1.writebyte(0b10000000 | (code // (1 << 0)) & 0b111111)
                    dst += 2
                elif flag == 'epd':
                    c1 = 0b11000000 | (code // (1 << 6)) & 0b11111
                    c2 = 0b10000000 | (code // (1 << 0)) & 0b111111
                    f_dwwrite_epd(dst, c1 + c2 * 256 + 0xD0D0000)
            if EUDElse()():  # Encode as 3-byte
                if flag == 'ptr':
                    bw1.writebyte(0b11100000 | (code // (1 << 12)) & 0b1111)
                    bw1.writebyte(0b10000000 | (code // (1 << 6)) & 0b111111)
                    bw1.writebyte(0b10000000 | (code // (1 << 0)) & 0b111111)
                    dst += 3
                elif flag == 'epd':
                    c1 = 0b11100000 | (code // (1 << 12)) & 0b1111
                    c2 = 0b10000000 | (code // (1 << 6)) & 0b111111
                    c3 = 0b10000000 | (code // (1 << 0)) & 0b111111
                    f_dwwrite_epd(dst, c1 + c2 * 256 + c3 * 65536 + 0xD000000)
            EUDEndIf()
        EUDEndIf()
        if flag == 'epd':
            dst += 1
    EUDEndInfLoop()
    if flag == 'ptr':
        bw1.writebyte(0)
        bw1.flushdword()

    return dst


class f_str:  # f_dbstr_addstr
    def __init__(self, value):
        self._value = value


class f_s2u:  # f_cp949_to_utf8_copy
    def __init__(self, value):
        self._value = value


def p(x):
    if isUnproxyInstance(x, type(P1)):
        if x == CurrentPlayer:
            x = f_getcurpl()
        else:
            x = EncodePlayer(x)
    return x


def f_color(x):  # f_dbstr_addstr(Color[x])
    return f_str(Color[p(x)])


class f_1c:  # _epd함수에서 1글자씩 쓰기
    def __init__(self, value):
        self._value = value


class f_get:  # ptr/epd 중간 저장
    def __init__(self, value):
        self._value = value


def Name(x):
    return f_str(0x57EEEB + 36 * p(x))


def process_bytes(s):
    while len(s) % 4 == 0:
        s += b'\x0D'
    DoActions([[
        SetDeaths(CurrentPlayer, SetTo, f_b2i(s[i:i+4]), 0),
        SetMemory(0x6509B0, Add, 1),
    ] for i in range(0, len(s), 4)])


def f_cp949_print(dst, *args):
    if isUnproxyInstance(dst, DBString):
        dst = dst.GetStringMemoryAddr()

    args = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, f_str) or isUnproxyInstance(arg, f_s2u):
            dst = f_dbstr_addstr(dst, arg._value)
        elif isUnproxyInstance(arg, f_get):
            SetVariables(arg._value, dst)
        else:
            dst = f_dbstr_print(dst, arg)

    return dst


def f_utf8_print(dst, *args):
    if isUnproxyInstance(dst, DBString):
        dst = dst.GetStringMemoryAddr()
    args = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, f_s2u):
            dst = f_cp949_to_utf8_copy(dst, arg._value)
        elif isUnproxyInstance(arg, str):
            dst = f_dbstr_addstr(dst, Db(u2utf8(arg) + b'\0'))
        else:
            dst = f_cp949_print(dst, arg)

    return dst


def f_sprintf(dst, *args):  # 버전 호환 f_dbstr_print
    ret = EUDVariable()
    if EUDIf()(f_is116()):
        ret << f_cp949_print(dst, *args)
    if EUDElse()():
        ret << f_utf8_print(dst, *args)
    EUDEndIf()

    return ret


@EUDFunc
def f_reset():  # ptr, epd를 스트링 시작 주소로 설정합니다.
    RawTrigger(
        actions=[write_ptr << ptr.SetNumber(0),
                 write_epd << epd.SetNumber(0)])


def f_addText(*args):
    ptr << f_sprintf(ptr, *args)


def f_makeText(*args):
    f_reset()
    f_addText(*args)


@EUDFunc
def f_displayText():
    DoActions(DisplayText(strBuffer))


@EUDFunc
def f_displayTextP(player):
    f_getoldcp()
    DoActions([
        SetMemory(0x6509B0, SetTo, player),
        DisplayText(strBuffer)
    ])
    f_setoldcp()


@EUDFunc
def f_displayTextAll():
    f_getoldcp()
    f_setlocalcp()
    DoActions(DisplayText(strBuffer))
    f_setoldcp()


def f_print(*args):
    f_makeText(*args)
    DoActions(DisplayText(strBuffer))


def f_printP(player, *args):
    f_makeText(*args)
    f_displayTextP(player)


def f_printAll(*args):
    f_makeText(*args)
    f_displayTextAll()


def f_playSound(*args):
    f_makeText(*args)
    DoActions(PlayWAV(strBuffer))


def f_playSoundP(player, *args):
    f_getoldcp()
    DoActions(SetMemory(0x6509B0, SetTo, player))
    f_playSound(*args)
    f_setoldcp()


def f_playSoundAll(*args):
    f_getoldcp()
    f_setlocalcp()
    f_playSound(*args)
    f_setoldcp()


@EUDFunc
def f_strptr(strID):  # getStringPtr
    r, m = f_div(strID, 2)
    RawTrigger(actions=AddSTR_epd << r.AddNumber(0))
    ret = f_wread_epd(r, m * 2)  # strTable_epd + r
    RawTrigger(actions=AddSTR_ptr << ret.AddNumber(0))
    EUDReturn(ret)  # strTable_ptr + strOffset


@EUDFunc
def f_reset_epd():
    bw1.seekoffset(f_strptr(strBuffer))
    for _ in EUDLoopRange(nmod):
        bw1.writebyte(0xD)
    bw1.flushdword()


def f_init():
    SetVariables([STR_ptr, STR_epd],
                 f_dwepdread_epd(EPD(0x5993D4)))
    localcp = f_dwread_epd(EPD(0x57F1B0))
    DoActions([
        SetMemory(setlocalcp + 20, SetTo, localcp),
        cp.SetNumber(localcp),
        SetMemory(AddSTR_ptr + 20, SetTo, STR_ptr),
        SetMemory(AddSTR_epd + 20, SetTo, STR_epd),
        nmod.SetNumber(4 - f_strptr(strBuffer) % 4)
    ])
    f_reset_epd()
    DoActions([
        SetMemory(write_ptr + 20, SetTo, f_strptr(strBuffer)),
        SetMemory(write_epd + 20, SetTo, EPD(f_strptr(strBuffer) + nmod))
    ])
    f_reset()
    f_setlocalcp()  # prevent Forward Not initialized
    f_setoldcp()
    if EUDIf()(Never()):
        f_TBLinit()
    EUDEndIf()


EUDOnStart(f_init)


@EUDFunc
def f_printError(player):
    if EUDIf()(Memory(0x628438, Exactly, 0)):
        EUDReturn()
    EUDEndIf()
    restorePtr = Forward()
    RawTrigger(actions=SetMemory(restorePtr + 20, SetTo, 0x59CCA8))
    for i in range(10, -1, -1):
        RawTrigger(
            conditions=Memory(0x628438, AtLeast, 0x59CCA8 + 336 * 2**i),
            actions=[
                SetMemory(0x628438, Subtract, 336 * 2**i),
                SetMemory(restorePtr + 20, Add, 336 * 2**i)
            ])
    DoActions([
        SetMemory(0x628438, SetTo, 0),
        CreateUnit(1, 0, 1, player),
        restorePtr << SetMemory(0x628438, SetTo, 0)
    ])


@EUDFunc
def f_chatdst_EUDVar(line):
    EUDReturn(0x640B60 + 218 * line)


def f_chatdst(line):
    if isUnproxyInstance(line, int):
        return 0x640B60 + 218 * line
    else:
        return f_chatdst_EUDVar(line)


def f_addChat(*args):
    chatptr << f_sprintf(chatptr, *args)


def f_chatprint(line, *args):
    if isinstance(line, int) and line == 12:
        f_printError(EncodePlayer(CurrentPlayer))
    if EUDIf()(Memory(0x57F1B0, Exactly, f_getcurpl())):
        chatptr << f_sprintf(f_chatdst(line), *args)
    EUDEndIf()


def f_chatprintP(player, line, *args):
    if isinstance(line, int) and line == 12:
        f_printError(player)
    if EUDIf()(Memory(0x57F1B0, Exactly, player)):
        chatptr << f_sprintf(f_chatdst(line), *args)
    EUDEndIf()


def f_chatprintAll(line, *args):
    if isinstance(line, int) and line == 12:
        f_printError(EncodePlayer(AllPlayers))
    chatptr << f_sprintf(f_chatdst(line), *args)


@EUDFunc
def f_addstr_epd(dstp, src):
    br1.seekoffset(src)

    if EUDInfLoop()():
        b1 = br1.readbyte()
        EUDBreakIf(b1 == 0)
        f_dwwrite_epd(dstp, b1)
        if EUDIf()(b1 <= 0x7F):
            f_dwadd_epd(dstp, 0x0D0D0D00)
        if EUDElse()():
            b2 = br1.readbyte()
            f_dwadd_epd(dstp, b2 * 0x100)
            if EUDIf()(b1 <= 0xDF):  # Encode as 2-byte
                f_dwadd_epd(dstp, 0x0D0D0000)
            if EUDElse()():  # 3-byte
                b3 = br1.readbyte()
                f_dwadd_epd(dstp, b3 * 0x10000)
                f_dwadd_epd(dstp, 0x0D000000)
            EUDEndIf()
        EUDEndIf()
        dstp += 1
    EUDEndInfLoop()
    return dstp


def f_addbyte_epd(dstp, b):
    while len(b) % 4 >= 1:
        b = b + b"\x0D"
    for i in range(len(b) // 4):
        f_dwwrite_epd(dstp, f_b2i(b[4 * i:4 * (i + 1)]))
        dstp += 1
    return dstp


def f_strbyte_epd(dstp, s, encoding='UTF-8'):
    b = s.encode(encoding)
    return f_addbyte_epd(dstp, b)


def f_add1c_epd(dstp, s, encoding='UTF-8'):
    string = ""
    color = ""
    for i, c in enumerate(s):
        c_ = c.encode(encoding)
        ci = f_b2i(c_)
        if (ci >= 0x01 and ci <= 0x1F and
                ci != 0x12 and ci != 0x13):
            color = c
            if i - 1 == len(s):
                string += color
            continue

        if string == "" and color != "":
            string += "\x0D\x0D\x0D"
        string += color + c

        for _ in range(3 - len(c_)):
            string += "\x0D"

        if color == "":
            color = "\x0D"

    return f_strbyte_epd(dstp, string, encoding)


@EUDFunc
def f_adddw_epd(dstp, number):
    skipper = [Forward() for _ in range(9)]
    ch = [0] * 10

    for i in range(10):  # Get digits
        number, ch[i] = f_div(number, 10)
        if i != 9:
            EUDJumpIf(number == 0, skipper[i])

    for i in range(9, -1, -1):  # print digits
        if i != 9:
            skipper[i] << NextTrigger()
        f_dwwrite_epd(dstp, ch[i] + b'0'[0] + 0xD0D0D00)
        dstp += 1

    return dstp


@EUDFunc
def f_addptr_epd(dstp, number):
    ch = [0] * 8
    for i in range(8):
        number, ch[i] = f_div(number, 16)

    for i in range(7, -1, -1):
        if EUDIf()(ch[i] <= 9):
            f_dwwrite_epd(dstp, ch[i] + b'0'[0] + 0xD0D0D00)
        if EUDElse()():
            f_dwwrite_epd(dstp, ch[i] + (b'A'[0] - 10) + 0xD0D0D00)
        EUDEndIf()
        dstp += 1

    return dstp


def f_cp949_print_epd(dstp, *args):
    arg = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, f_str) or isUnproxyInstance(arg, f_s2u):
            dstp = f_addstr_epd(dstp, arg._value)
        elif isUnproxyInstance(arg, f_1c):
            dstp = f_add1c_epd(dstp, arg._value, encoding="cp949")
        elif isUnproxyInstance(arg, f_get):
            SetVariables(arg._value, dstp)
        elif isUnproxyInstance(arg, bytes):
            dstp = f_addbyte_epd(dstp, arg)
        elif isUnproxyInstance(arg, str):
            dstp = f_strbyte_epd(dstp, arg, encoding="cp949")
        elif isUnproxyInstance(arg, DBString):
            dstp = f_addstr_epd(dstp, arg.GetStringMemoryAddr())
        elif isUnproxyInstance(arg, int):
            dstp = f_addstr_epd(dstp, Db(u2b(str(arg & 0xFFFFFFFF)) + b'\0'))
        elif isUnproxyInstance(arg, EUDVariable) or IsConstExpr(arg):
            dstp = f_adddw_epd(dstp, arg)
        elif isUnproxyInstance(arg, hptr):
            dstp = f_addptr_epd(dstp, arg._value)
        else:
            raise EPError('unknown parameter type %s given to print_epd.'
                          % type(arg))
    f_dwwrite_epd(dstp, 0)
    return dstp


def f_utf8_print_epd(dstp, *args):
    arg = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, str):
            dstp = f_strbyte_epd(dstp, arg)
        elif isUnproxyInstance(arg, f_s2u):
            dstp = f_cp949_to_utf8_copy(dstp, arg._value, 'epd')
        elif isUnproxyInstance(arg, f_1c):
            dstp = f_add1c_epd(dstp, arg._value)
        else:
            dstp = f_cp949_print_epd(dstp, arg)
    f_dwwrite_epd(dstp, 0)
    return dstp


def f_sprintf_epd(dstp, *args):
    ret = EUDVariable()
    if EUDIf()(f_is116()):
        ret << f_cp949_print_epd(dstp, *args)
    if EUDElse()():
        ret << f_utf8_print_epd(dstp, *args)
    EUDEndIf()

    return ret


def f_byteTest(s, e="UTF-8"):
    s = s.encode(e)
    while len(s) % 4 >= 1:
        s += b'\x00'
    for i in range(math.ceil(len(s) / 4)):
        print("{}: {}".format(i, s[4 * i:min([4 * (i + 1), len(s)])]))


def f_addText_epd(*args):
    epd << f_sprintf_epd(epd, *args)


def f_makeText_epd(*args):
    f_reset()
    f_reset_epd()
    f_addText_epd(*args)


def f_print_epd(*args):
    f_makeText_epd(*args)
    f_displayText()


def f_printP_epd(player, *args):
    f_makeText_epd(*args)
    f_displayTextP(player)


def f_printAll_epd(*args):
    f_makeText_epd(*args)
    f_displayTextAll()


@EUDFunc
def f_chatepd_EUDVar(line):
    r, m = f_div(line, 2)
    if EUDIf()(m == 0):
        EUDReturn(EPD(0x640B60) + 109 * r)
    if EUDElse()():
        EUDReturn(EPD(0x640C3A) + 109 * r)
    EUDEndIf()


def f_chatepd(line):
    if isUnproxyInstance(line, int):
        return EPD(0x640B60 + 218 * line)
    else:
        return f_chatepd_EUDVar(line)


def f_addChat_epd(*args):
    chatepd << f_sprintf_epd(chatepd, *args)


def f_chatprint_epd(line, *args):
    if isinstance(line, int) and line == 12:
        f_printError(EncodePlayer(CurrentPlayer))
    if EUDIf()(Memory(0x57F1B0, Exactly, f_getcurpl())):
        chatepd << f_sprintf_epd(f_chatepd(line), *args)
    EUDEndIf()


def f_chatprintP_epd(player, line, *args):
    if isinstance(line, int) and line == 12:
        f_printError(player)
    if EUDIf()(Memory(0x57F1B0, Exactly, player)):
        chatepd << f_sprintf_epd(f_chatepd(line), *args)
    EUDEndIf()


def f_chatprintAll_epd(line, *args):
    if isinstance(line, int) and line == 12:
        f_printError(EncodePlayer(AllPlayers))
    chatepd << f_sprintf_epd(f_chatepd(line), *args)


@EUDFunc
def f_dbstr_addstr2(dst, src):
    b = EUDVariable()
    br1.seekoffset(src)
    bw1.seekoffset(dst)

    if EUDInfLoop()():
        SetVariables(b, br1.readbyte())
        EUDBreakIf(b == 0)
        bw1.writebyte(b)
        dst += 1
    EUDEndInfLoop()

    bw1.flushdword()
    return dst


@EUDFunc
def f_dbstr_adddw2(dst, number, length):
    bw1.seekoffset(dst)
    skipper = [Forward() for _ in range(9)]
    ch = [0] * 10

    for i in range(10):  # Get digits
        number, ch[i] = f_div(number, 10)
        if i != 9:
            EUDJumpIf(length == i + 1, skipper[i])
            EUDJumpIf(number == 0, skipper[i])

    for i in range(9, -1, -1):  # print digits
        if i != 9:
            skipper[i] << NextTrigger()
        bw1.writebyte(ch[i] + b'0'[0])
        dst += 1
    bw1.flushdword()
    return dst


def f_dbstr_print2(dst, length, *args):
    if isinstance(dst, DBString):
        dst = dst.GetStringMemoryAddr()

    args = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, bytes):
            dst = f_dbstr_addstr2(dst, Db(arg + b'\0'))
        elif isUnproxyInstance(arg, str):
            dst = f_dbstr_addstr2(dst, Db(u2b(arg) + b'\0'))
        elif isUnproxyInstance(arg, DBString):
            dst = f_dbstr_addstr2(dst, arg.GetStringMemoryAddr())
        elif isUnproxyInstance(arg, int):
            dst = f_dbstr_addstr2(dst, Db(u2b(str(arg & 0xFFFFFFFF)) + b'\0'))
        elif isUnproxyInstance(arg, EUDVariable) or IsConstExpr(arg):
            dst = f_dbstr_adddw2(dst, arg, length)
        elif isUnproxyInstance(arg, f_str):
            dst = f_dbstr_addstr2(dst, arg._value)
        else:
            dst = f_cp949_print(dst, arg)

    return dst


TBL_ptr, TBL_epd = EUDCreateVariables(2)
AddTBL_ptr, AddTBL_epd = Forward(), Forward()
_initTbl = EUDLightVariable(0)
_tbl_start, _tbl_end, _return_from_whence_thou_camst = Forward(), Forward(), Forward()


@EUDFunc
def f_tblptr(tblID):
    r, m = f_div(tblID, 2)
    RawTrigger(actions=AddTBL_epd << r.AddNumber(0))
    ret = f_wread_epd(r, m * 2)  # strTable_epd + r
    RawTrigger(actions=AddTBL_ptr << ret.AddNumber(0))
    return ret  # tbl_ptr + tblOffset


def f_TBLinit():
    _tbl_start << NextTrigger()
    SetVariables([TBL_ptr, TBL_epd],
                 f_dwepdread_epd(EPD(0x6D5A30)))
    DoActions([
        SetMemory(AddTBL_epd + 20, SetTo, TBL_epd),
        SetMemory(AddTBL_ptr + 20, SetTo, TBL_ptr)])

    f_tblptr(0)  # prevent Forward Not initialized
    _tbl_end << RawTrigger(
        actions=[
            _initTbl.SetNumber(1),
            _return_from_whence_thou_camst << SetNextPtr(0xEDAC, 0xF001)
        ]
    )


def f_setTbl(tblID, offset, length, *args):
    _is_tbl_init, _next = Forward(), Forward()
    _is_tbl_init << RawTrigger(
        conditions=_initTbl.Exactly(0),
        actions=[
            SetNextPtr(_is_tbl_init, _tbl_start),
            SetNextPtr(_tbl_end, _next),
            SetMemory(_return_from_whence_thou_camst + 16, SetTo, EPD(_is_tbl_init + 4)),
            SetMemory(_return_from_whence_thou_camst + 20, SetTo, _next)
        ]
    )
    _next << NextTrigger()
    dst = f_tblptr(tblID) + offset
    f_dbstr_print2(dst, length, *args)


# legacy
colorArray = Color
f_getTblPtr = f_tblptr
f_ct_print = f_utf8_print
f_ct_print_epd = f_utf8_print_epd
f_cprint = f_sprintf
f_cprint_epd = f_sprintf_epd


def f_chatAnnouncement(*args):
    f_chatprint(12, *args)


def f_chatAnnouncement_epd(*args):
    f_chatprint_epd(12, *args)


def f_legacySupport():
    global legacySupport
    legacySupport = 1
