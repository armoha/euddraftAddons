from eudplib import *
from eudplib.eudlib.stringf.rwcommon import br1, bw1
import eudplib.eudlib.stringf.cputf8 as cputf
import math


# 내부적으로 쓰는 함수들입니다. 어려울 수 있으니 무시해요 ///////////////////////
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
                    f_dwwrite_epd(dstp, c1 + c2 * 256 + 0xD0D0000)
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
                    f_dwwrite_epd(dstp, c1 + c2 * 256 + c3 * 65536 + 0xD000000)
            EUDEndIf()
        EUDEndIf()
        if flag == 'epd':
            dst += 1
    EUDEndInfLoop()
    if flag == 'ptr':
        bw1.writebyte(0)
        bw1.flushdword()

    return dst


def _CGFW(exprf, retn):
    rets = [ExprProxy(None) for _ in range(retn)]

    def _():
        vals = exprf()
        for ret, val in zip(rets, vals):
            ret._value = val
    EUDOnStart(_)
    return rets


def u2u(s):
    if isinstance(s, str):
        return s.encode('UTF-8')
    elif isinstance(s, bytes):
        return s
    else:
        raise EPError('Invalid type %s' % type(s))


def b2i(byte):
    return int.from_bytes(byte, 'little')


# 내부 클래스?
class f_str:  # f_dbstr_addstr
    def __init__(self, value):
        self._value = value


class f_s2u:  # f_cp949_to_utf8_copy
    def __init__(self, value):
        self._value = value


class f_color:  # f_dbstr_addstr(colorArray[i])
    def __init__(self, value):
        self._value = value


class f_byte:
    def __init__(self, value):
        self._value = value


class f_str2:
    def __init__(self, value):
        self._value = value


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
        elif isUnproxyInstance(arg, f_color):
            dst = f_dbstr_addstr2(dst, colorArray[arg._value])
        elif isUnproxyInstance(arg, f_str):
            dst = f_dbstr_addstr2(dst, arg._value)
        elif isUnproxyInstance(arg, f_s2u):
            dst = f_cp949_to_utf8_copy(dst, arg._value)
        elif isUnproxyInstance(arg, f_str2):
            dst = f_dbstr_addstr(dst, arg._value)
        elif isUnproxyInstance(arg, f_byte):
            f_bwrite(dst, arg._value)
            dst += 1
        elif isUnproxyInstance(arg, hptr):
            dst = f_dbstr_addptr(dst, arg._value)
        else:
            raise EPError(
                'Object with unknown parameter type %s given to f_eudprint.'
                % type(arg)
            )

    return dst


# stat_txt.tbl 수정 관련 변수, 함수 //////////////////////////////////
colorArray = EUDArray([
    Db(b'\x08\0'), Db(b'\x0E\0'), Db(b'\x0F\0'), Db(b'\x10\0'),
    Db(b'\x11\0'), Db(b'\x15\0'), Db(b'\x16\0'), Db(b'\x17\0'),
    Db(b'\x18\0'), Db(b'\x19\0'), Db(b'\x1B\0'), Db(b'\x1C\0'),
    Db(b'\x1D\0'), Db(b'\x1E\0'), Db(b'\x1F\0')
])
tbl_ptr, tbl_epd = EUDCreateVariables(2)
add_tblepd, add_tblptr = [Forward() for _ in range(2)]


@EUDFunc
def f_getTblPtr(tblID):
    r, m = f_div(tblID, 2)
    RawTrigger(actions=add_tblepd << r.AddNumber(0))
    ret = f_wread_epd(r, m * 2)  # strTable_epd + r
    RawTrigger(actions=add_tblptr << ret.AddNumber(0))
    EUDReturn(ret)  # tbl_ptr + tblOffset


def f_setTbl(tblID, offset, length, *args):
    dst = f_getTblPtr(tblID) + offset
    dst = f_dbstr_print2(dst, length, *args)


# 변수 목록 ///////////////////////////////////////////////////////////
isLegacy = 0
strBuffer = _CGFW(lambda: [GetStringIndex("i" * 600)], 1)[0]
strTable_ptr, strTable_epd = EUDCreateVariables(2)
ptr, epd, cp, nmod = EUDCreateVariables(4)
add_sTepd, add_sTptr, SetPtr, SetEPD = [Forward() for _ in range(4)]


@EUDFunc
def f_strptr(strID):  # 스트링 주소를 가져옵니다. (getStringPtr)
    r, m = f_div(strID, 2)
    RawTrigger(actions=add_sTepd << r.AddNumber(0))
    ret = f_wread_epd(r, m * 2)  # strTable_epd + r
    RawTrigger(actions=add_sTptr << ret.AddNumber(0))
    EUDReturn(ret)  # strTable_ptr + strOffset


@EUDFunc
def f_reset():  # ptr, epd를 스트링 시작 주소로 설정합니다.
    RawTrigger(
        actions=[SetPtr << ptr.SetNumber(0),
                 SetEPD << epd.SetNumber(0)])


@EUDFunc
def f_reset_epd():
    bw1.seekoffset(f_strptr(strBuffer))
    for i in EUDLoopRange(nmod):
        bw1.writebyte(0xD)
    bw1.flushdword()


def f_legacySupport():
    global isLegacy
    isLegacy = 1


def f_init():  # 자동 실행됩니다.
    SetVariables([tbl_ptr, tbl_epd], f_dwepdread_epd(EPD(0x6D5A30)))
    DoActions([SetMemory(add_tblepd + 20, SetTo, tbl_epd),
               SetMemory(add_tblptr + 20, SetTo, tbl_ptr)])
    SetVariables([strTable_ptr, strTable_epd],
                 f_dwepdread_epd(EPD(0x5993D4)))
    cp << f_dwread_epd(EPD(0x57F1B0))
    DoActions([SetMemory(add_sTepd + 20, SetTo, strTable_epd),
               SetMemory(add_sTptr + 20, SetTo, strTable_ptr)])
    nmod << 4 - f_strptr(strBuffer) % 4
    f_reset_epd()
    DoActions([SetMemory(SetPtr + 20, SetTo, f_strptr(strBuffer)),  # + nmod),
               SetMemory(SetEPD + 20, SetTo, EPD(f_strptr(strBuffer) + nmod))])
    f_reset()
    a = f_getTblPtr(0)


EUDOnStart(f_init)


def f_ct_print(dst, *args):
    args = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, f_str):
            dst = f_dbstr_addstr(dst, arg._value)
        elif isUnproxyInstance(arg, f_s2u):
            dst = f_cp949_to_utf8_copy(dst, arg._value)
        elif isUnproxyInstance(arg, f_color):
            dst = f_dbstr_addstr(dst, colorArray[arg._value])
        elif isUnproxyInstance(arg, f_byte):
            f_bwrite(dst, arg._value)
            dst += 1
        elif isUnproxyInstance(arg, str):
            dst = f_dbstr_addstr(dst, Db(u2u(arg) + b'\0'))
        else:
            dst = f_dbstr_print(dst, arg)

    return dst


def f_cprint(dst, *args):  # compatible print
    end = Db(b'\0')
    if EUDIf()(Memory(0x51CE84, AtMost, 99)):
        ptr << f_dbstr_print2(dst, -1, *(args + (f_str2(end), )))
    if EUDElse()():
        ptr << f_ct_print(dst, *args)
    EUDEndIf()


def f_addText(*args):  # 스트링의 맨 뒤에 덧붙입니다.
    if isLegacy == 1:
        f_cprint(ptr, *args)
    else:
        ptr << f_ct_print(ptr, *args)


def f_makeText(*args):  # 스트링을 처음부터 새로 씁니다.
    f_reset()
    f_addText(*args)


def f_displayText(player):  # player에게 있는 텍스트를 출력합니다.
    oldcp = f_getcurpl()
    f_setcurpl(player)
    DoActions(DisplayText(strBuffer))
    f_setcurpl(oldcp)


def f_print(*args):  # CurrentPlayer에게 텍스트를 만들어 출력합니다.
    f_makeText(*args)
    DoActions(DisplayText(strBuffer))


def f_printP(player, *args):  # player에게 텍스트를 만들어 출력합니다.
    f_makeText(*args)
    f_displayText(player)


@EUDFunc
def f_printError(player):
    nextPtr = f_dwread_epd(EPD(0x628438))
    DoActions([
        SetMemoryEPD(EPD(0x628438), SetTo, 0),
        CreateUnit(1, 0, 1, player),
        SetMemoryEPD(EPD(0x628438), SetTo, nextPtr)
    ])


def f_chatdst(line):
    return 0x640B60 + 218 * line


def f_chatwrite(line, s, e="UTF-8"):
    chatdst = EPD(f_chatdst(line))
    s = s.encode(e)
    if line % 2 == 1:
        s = b'\x00\x00' + s
    while len(s) % 4 >= 1:
        s = s + b'\x0D'
    s = s + b'\x00'

    for i in range(math.ceil(len(s) / 4)):
        f_dwwrite_epd(chatdst + i, b2i(s[4 * i:min([4 * (i + 1), len(s)])]))


def f_chatprint(line, *args):
    if isLegacy == 1:
        f_cprint(f_chatdst(line), *args)
    else:
        f_ct_print(f_chatdst(line), *args)


def f_chatDisplay(player, line, *args):
    if line == 12:
        f_printError(player)
    if isinstance(player, int):
        if player >= 8:
            f_chatprint(line, *args)
        else:
            if EUDIf()(Memory(0x57F1B0, Exactly, player)):
                f_chatprint(line, *args)
            EUDEndIf()
    else:
        if EUDIf()(Memory(0x57F1B0, Exactly, player)):
            f_chatprint(line, *args)
        EUDEndIf()


def f_byteTest(s, e="UTF-8"):
    s = s.encode(e)
    while len(s) % 4 >= 1:
        s += b'\x00'
    for i in range(math.ceil(len(s) / 4)):
        print("{}: {}".format(i, s[4 * i:min([4 * (i + 1), len(s)])]))


# 내부 epd 함수들
@EUDFunc
def f_addstr_epd(dstp, src):
    b1, b2, b3 = EUDCreateVariables(3)
    br1.seekoffset(src)

    if EUDInfLoop()():
        b1 << br1.readbyte()
        EUDBreakIf(b1 == 0)
        if EUDIf()(b1 <= 0x7F):
            DoActions([SetMemoryEPD(dstp, SetTo, b1),
                       SetMemoryEPD(dstp, Add, 0x0D0D0D00)])
        if EUDElse()():
            b2 << br1.readbyte()
            if EUDIf()(b1 <= 0xDF):  # Encode as 2-byte
                DoActions([SetMemoryEPD(dstp, SetTo, b1),
                           SetMemoryEPD(dstp, Add, b2 * 0x100),
                           SetMemoryEPD(dstp, Add, 0x0D0D0000)])
            if EUDElse()():
                b3 << br1.readbyte()
                DoActions([SetMemoryEPD(dstp, SetTo, b1),
                           SetMemoryEPD(dstp, Add, b2 * 0x100),
                           SetMemoryEPD(dstp, Add, b3 * 0x10000),
                           SetMemoryEPD(dstp, Add, 0x0D000000)])
            EUDEndIf()
        EUDEndIf()
        dstp += 1
    EUDEndInfLoop()
    EUDReturn(dstp)


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


def addbyte_epd(dstp, byte, flag=1):
    if flag == 1:
        while len(byte) % 4 >= 1:
            byte = byte + b'\x0D'
    for i in range(math.ceil(len(byte) / 4)):
        f_dwwrite_epd(dstp, b2i(byte[4 * i:min([4 * (i + 1), len(byte)])]))
        dstp += 1
    return dstp


def f_ct_print_epd(dstp, *args):
    arg = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, f_str):
            dstp = f_addstr_epd(dstp, arg._value)
        elif isUnproxyInstance(arg, f_s2u):
            dstp = f_cp949_to_utf8_copy(dstp, arg._value, 'epd')
        elif isUnproxyInstance(arg, f_color):
            dstp = f_addstr_epd(dstp, colorArray[arg._value])
        elif isUnproxyInstance(arg, bytes):
            dstp = addbyte_epd(dstp, arg)
        elif isUnproxyInstance(arg, str):
            dstp = addbyte_epd(dstp, arg.encode("UTF-8"))
        elif isUnproxyInstance(arg, DBString):
            dstp = f_addstr_epd(dstp, arg.GetStringMemoryAddr())
        elif isUnproxyInstance(arg, int):
            dstp = addbyte_epd(dstp, str(arg).encode("UTF-8"))
        elif isUnproxyInstance(arg, EUDVariable) or IsConstExpr(arg):
            dstp = f_adddw_epd(dstp, arg)
        elif isUnproxyInstance(arg, hptr):
            dstp = f_addptr_epd(dstp, arg._value)
        else:
            raise EPError('unknown parameter type %s given to ct_print_epd.'
                          % type(arg))
    f_dwwrite_epd(dstp, 0)
    return dstp


def f_addText_epd(*args):
    epd << f_ct_print_epd(epd, *args)


def f_makeText_epd(*args):
    f_reset()
    f_addText_epd(*args)


def f_print_epd(*args):
    f_makeText_epd(*args)
    DoActions(DisplayText(strBuffer))


def f_printP_epd(player, *args):
    f_makeText_epd(*args)
    f_displayText(player)


def f_playSound(*args):
    f_makeText(*args)
    DoActions(PlayWAV(strBuffer))


def f_playSoundP(player, *args):
    oldcp = f_getcurpl()
    f_setcurpl(player)
    f_playSound(*args)
    f_setcurpl(oldcp)
