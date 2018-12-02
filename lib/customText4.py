# -*- coding: utf-8 -*-
import math

import eudplib.eudlib.stringf.cputf8 as cputf
from eudplib import *
from eudplib.core.curpl import _curpl_var
from eudplib.eudlib.stringf.rwcommon import br1, bw1


"""
customText 0.3.2

0.3.2 clean f_init
0.3.1 fix hptr, cpcache
0.3.0 Add CPString, f_cpprint
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
    return int.from_bytes(x, byteorder="little")


CP = 0x6509B0
chkt = GetChkTokenized()
STR = chkt.getsection("STR")
lenSTR2 = b2i2(STR[6:8]) - 2 * b2i2(STR[0:2])
if lenSTR2 < 218:
    print(
        """*경고* 현재 1번 스트링 길이: {}
다른 스트링 덮어쓰기를 방지하려면
맵 소개를 218자 이상으로 두는걸 권장합니다.""".format(
            lenSTR2
        )
    )


def _s2b(x):
    if isinstance(x, str):
        x = u2utf8(x)
    if isinstance(x, bytes):
        x = x + b"\r" * (-(-len(x) // 4) * 4 - len(x))
    return x


class CPString:
    """
    store String in SetDeaths Actions, easy to concatenate
    """

    def __init__(self, content=None):
        """Constructor for CPString
        :param content: Initial CPString content / capacity. Capacity of
            CPString is determined by size of this. If content is integer, then
            initial capacity and content of CPString will be set to
            content(int) and empty string.
        :type content: str, bytes, int
        """
        if isinstance(content, int):
            self.content = b"\r" * -(-content // 4) * 4
        elif isinstance(content, str) or isinstance(content, bytes):
            self.content = _s2b(content)
        else:
            raise EPError("Unexpected type for CPString: {}".format(type(content)))

        self.length = len(content) // 4
        self.trigger = list()
        self.valueAddr = list()
        actions = FlattenList([
            [
                SetDeaths(CurrentPlayer, SetTo, f_b2i(self.content[i : i + 4]), 0),
                SetMemory(CP, Add, 1),
            ]
            for i in range(0, len(self.content), 4)
        ])
        for i in range(0, len(actions), 64):
            t = RawTrigger(actions=actions[i : i + 64])
            self.trigger.append(t)
            self.valueAddr.extend(
                [
                    t + (8 + 320 + 20) + 64 * k
                    for k in range(min(32, (len(actions) - i) // 2))
                ]
            )

    def GetVTable(self):
        return self.trigger[0]

    def GetNextPtrMemory(self):
        return self.trigger[-1] + 4

    def Assign(self, content):
        if isinstance(content, int):
            content = b"\r" * -(-content // 4) * 4
        elif isinstance(content, str) or isinstance(content, bytes):
            content = _s2b(content)
        else:
            raise EPError("Unexpected type for CPString: {}".format(type(content)))
        ret = list()
        for i in range(0, len(content), 4):
            ret.extend(
                [
                    SetMemory(
                        self.valueAddr[i // 4], SetTo, f_b2i(content[i : i + 4]), 0
                    ),
                    SetMemory(self.valueAddr[i // 4] + 4, SetTo, 0x072D0000, 0),
                ]
            )
        if len(content) % (4 * 32) >= 1:
            ret.append(
                SetMemory(
                    self.valueAddr[len(content) // 4 - 1] + 68, SetTo, 0x07000000, 0
                )
            )
        self.content = content
        return ret


class CPByteWriter:
    """Write byte by byte"""

    def __init__(self):
        self._suboffset = EUDVariable()
        self._b = [EUDLightVariable(f_b2i(b"\r")) for _ in range(4)]

    @EUDMethod
    def writebyte(self, byte):
        """Write byte to current position.

        Write a byte to current position of EUDByteWriter. Writer will advance
        by 1 byte.

        .. note::
            Bytes could be buffered before written to memory. After you
            finished using writebytes, you must call `flushdword` to flush the
            buffer.
        """
        EUDSwitch(self._suboffset)
        for i in range(3):
            if EUDSwitchCase()(i):
                DoActions([self._b[i].SetNumber(byte), self._suboffset.AddNumber(1)])
                EUDBreak()

        if EUDSwitchCase()(3):
            DoActions(self._b[3].SetNumber(byte))
            self.flushdword()

        EUDEndSwitch()

    @EUDMethod
    def flushdword(self):
        """Flush buffer."""
        # mux bytes
        DoActions(SetDeaths(CurrentPlayer, SetTo, 0, 0))

        for i in range(7, -1, -1):
            for j in range(4):
                RawTrigger(
                    conditions=[self._b[j].AtLeast(2 ** i)],
                    actions=[
                        self._b[j].SubtractNumber(2 ** i),
                        SetDeaths(CurrentPlayer, Add, 2 ** (i + j * 8), 0),
                    ],
                )
        DoActions(
            [
                SetMemory(CP, Add, 1),
                self._suboffset.SetNumber(0),
                [self._b[i].SetNumber(f_b2i(b"\r")) for i in range(4)],
            ]
        )


cw = CPByteWriter()
ptr, epd, cp = EUDCreateVariables(3)
player_colors = "\x08\x0E\x0F\x10\x11\x15\x16\x17\x18\x19\x1B\x1C\x1D\x1E\x1F"
Color = EUDArray([EPD(Db(u2b(x))) for x in player_colors])
strBuffer = 1


def f_setcachedcp():
    VProc(_curpl_var, [_curpl_var.QueueAssignTo(EPD(CP))])


def f_setlocalcp():
    VProc(cp, [cp.QueueAssignTo(EPD(CP))])


@EUDFunc
def f_is116():
    if EUDIf()(Memory(0x51CE84, AtMost, 99)):
        EUDReturn(1)
    if EUDElse()():
        EUDReturn(0)
    EUDEndIf()


@EUDFunc
def f_cp949_to_utf8_cpy(dst, src):
    br1.seekoffset(src)
    bw1.seekoffset(dst)

    if EUDInfLoop()():
        b1 = br1.readbyte()
        EUDBreakIf(b1 == 0)
        if EUDIf()(b1 < 128):
            bw1.writebyte(b1)
            dst += 1
        if EUDElse()():
            b2 = br1.readbyte()
            EUDBreakIf(b2 == 0)
            code = cputf.cvtb[b2 * 256 + b1]
            if EUDIf()(code <= 0x07FF):  # Encode as 2-byte
                bw1.writebyte(0b11000000 | (code // (1 << 6)) & 0b11111)
                bw1.writebyte(0b10000000 | (code // (1 << 0)) & 0b111111)
                dst += 2
            if EUDElse()():  # Encode as 3-byte
                bw1.writebyte(0b11100000 | (code // (1 << 12)) & 0b1111)
                bw1.writebyte(0b10000000 | (code // (1 << 6)) & 0b111111)
                bw1.writebyte(0b10000000 | (code // (1 << 0)) & 0b111111)
                dst += 3
            EUDEndIf()
        EUDEndIf()
    EUDEndInfLoop()
    bw1.writebyte(0)
    bw1.flushdword()

    return dst


@EUDFunc
def f_cp949_to_utf8_cpy_epd(dst, src):
    br1.seekoffset(src)

    if EUDInfLoop()():
        b1 = br1.readbyte()
        EUDBreakIf(b1 == 0)
        if EUDIf()(b1 < 128):
            f_dwwrite_epd(dst, b1 + 0xD0D0D00)
        if EUDElse()():
            b2 = br1.readbyte()
            EUDBreakIf(b2 == 0)
            code = cputf.cvtb[b2 * 256 + b1]
            if EUDIf()(code <= 0x07FF):  # Encode as 2-byte
                c1 = 0b11000000 | (code // (1 << 6)) & 0b11111
                c2 = 0b10000000 | (code // (1 << 0)) & 0b111111
                f_dwwrite_epd(dst, c1 + c2 * 256 + 0xD0D0000)
            if EUDElse()():  # Encode as 3-byte
                c1 = 0b11100000 | (code // (1 << 12)) & 0b1111
                c2 = 0b10000000 | (code // (1 << 6)) & 0b111111
                c3 = 0b10000000 | (code // (1 << 0)) & 0b111111
                f_dwwrite_epd(dst, c1 + c2 * 256 + c3 * 65536 + 0xD000000)
            EUDEndIf()
        EUDEndIf()
        dst += 1
    EUDEndInfLoop()

    return dst


class f_str:  # f_dbstr_addstr
    def __init__(self, value):
        self._value = value


class f_s2u:  # f_cp949_to_utf8_cpy
    def __init__(self, value):
        self._value = value


class f_get:  # get ptr/epd in middle of string
    def __init__(self, value):
        self._value = value


class f_1c:
    def __init__(self, value):
        self._value = value


class f_strepd:  # EPD variation of f_dbstr_addstr
    def __init__(self, value):
        self._value = value


def f_color(i):  # f_dbstr_addstr(Color[i])
    return f_strepd(Color[i])


def Name(x):
    if x == CurrentPlayer:
        x = _curpl_var
    if isUnproxyInstance(x, type(P1)):
        x = EncodePlayer(x)
    return f_str(0x57EEEB + 36 * x)


def f_addbyte_cp(b):
    while len(b) % 4 >= 1:
        b = b + b"\x0D"
    DoActions(
        [
            [
                SetDeaths(CurrentPlayer, SetTo, f_b2i(b[i : i + 4]), 0),
                SetMemory(CP, Add, 1),
            ]
            for i in range(0, len(b), 4)
        ]
    )
    return len(b) // 4


@EUDFunc
def f_addstr_cp(src):
    """Print string as string to CurrentPlayer

    :param src: Source address (Not EPD player)
    """
    b = EUDVariable()
    br1.seekoffset(src)
    if EUDInfLoop()():
        SetVariables(b, br1.readbyte())
        cw.writebyte(b)
        EUDBreakIf(b == 0)
    EUDEndInfLoop()

    cw.flushdword()


@EUDFunc
def f_addstr_cp_epd(epd):
    """Print string as string to CurrentPlayer

    :param epd: EPD player of Source address
    """
    b = EUDVariable()
    br1.seekepd(epd)
    if EUDInfLoop()():
        SetVariables(b, br1.readbyte())
        cw.writebyte(b)
        EUDBreakIf(b == 0)
    EUDEndInfLoop()

    cw.flushdword()


@EUDFunc
def f_adddw_cp(number):
    """Print number as string to CurrentPlayer.

    :param number: DWORD to print
    """
    skipper = [Forward() for _ in range(9)]
    ch = [0] * 10

    # Get digits
    for i in range(10):
        number, ch[i] = f_div(number, 10)
        if i != 9:
            EUDJumpIf(number == 0, skipper[i])

    # print digits
    for i in range(9, -1, -1):
        if i != 9:
            skipper[i] << NextTrigger()
        cw.writebyte(ch[i] + b"0"[0])

    cw.flushdword()


@EUDFunc
def f_addptr_cp(number):
    """Print number as string to CurrentPlayer.

    :param number: DWORD to print
    """
    digit = [EUDLightVariable() for _ in range(8)]
    DoActions(
        [
            [digit[i].SetNumber(0) for i in range(8)],
            SetDeaths(CurrentPlayer, SetTo, b2i4(b"0000"), 0),
        ]
    )

    def f(x):
        t = x % 16
        q, r = divmod(t, 4)
        return 2 ** (r + 8 * (3 - q))

    for i in range(31, -1, -1):
        RawTrigger(
            conditions=number.AtLeast(2 ** i),
            actions=[
                number.SubtractNumber(2 ** i),
                digit[i // 4].AddNumber(2 ** (i % 4)),
                SetDeaths(CurrentPlayer, Add, f(i), 0),
            ],
        )
        if i % 16 == 0:
            for j in range(4):
                RawTrigger(
                    conditions=digit[j + 4 * (i // 16)].AtLeast(10),
                    actions=SetDeaths(
                        CurrentPlayer, Add, (b"A"[0] - b":"[0]) * (256 ** (3 - j)), 0
                    ),
                )
            DoActions(
                [
                    SetMemory(CP, Add, 1),
                    [
                        SetDeaths(CurrentPlayer, SetTo, b2i4(b"0000"), 0)
                        if i == 16
                        else []
                    ],
                ]
            )


_constcpstr_dict = {}


def f_cpprint(*args):
    """Print multiple string / number to CurrentPlayer.

    :param args: Things to print

    """
    args = FlattenList(args)
    delta = 0
    for arg in args:
        if isUnproxyInstance(arg, str):
            arg = u2utf8(arg)
        elif isUnproxyInstance(arg, int):
            arg = u2b(str(arg & 0xFFFFFFFF))
        if isUnproxyInstance(arg, bytes):
            key = _s2b(arg)
            if key not in _constcpstr_dict:
                _constcpstr_dict[key] = CPString(arg)
            arg = _constcpstr_dict[key]
        if isUnproxyInstance(arg, CPString):
            delta += arg.length
            _next = Forward()
            RawTrigger(
                nextptr=arg.GetVTable(),
                actions=SetMemory(arg.GetNextPtrMemory(), SetTo, _next),
            )
            _next << NextTrigger()
        elif isUnproxyInstance(arg, f_str):
            f_addstr_cp(arg._value)
        elif isUnproxyInstance(arg, f_strepd):
            f_addstr_cp_epd(arg._value)
        elif isUnproxyInstance(arg, DBString):
            f_addstr_cp(arg.GetStringMemoryAddr())
        elif isUnproxyInstance(arg, EUDVariable) or IsConstExpr(arg):
            f_adddw_cp(arg)
        elif isUnproxyInstance(arg, hptr):
            f_addptr_cp(arg._value)
            delta += 2
        else:
            raise EPError(
                "Object with unknown parameter type %s given to f_cpprint." % type(arg)
            )
    DoActions(SetDeaths(CurrentPlayer, SetTo, 0, 0))
    return delta


@EUDFunc
def f_addstr_epd(dst, epd):
    """Print string as string to dst. Same as strcpy except of return value.

    :param dst: Destination address (Not EPD player)
    :param epd: EPD player of Source address

    :returns: dst + strlen(src)
    """
    b = EUDVariable()

    br1.seekepd(epd)
    bw1.seekoffset(dst)

    if EUDInfLoop()():
        SetVariables(b, br1.readbyte())
        bw1.writebyte(b)
        EUDBreakIf(b == 0)
        dst += 1
    EUDEndInfLoop()

    bw1.flushdword()

    return dst


def f_cp949_print(dst, *args):
    if isUnproxyInstance(dst, DBString):
        dst = dst.GetStringMemoryAddr()

    args = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, f_str):
            dst = f_dbstr_addstr(dst, arg._value)
        elif isUnproxyInstance(arg, f_strepd):
            dst = f_addstr_epd(dst, arg._value)
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
            dst = f_cp949_to_utf8_cpy(dst, arg._value)
        elif isUnproxyInstance(arg, str):
            dst = f_dbstr_addstr(dst, Db(u2utf8(arg) + b"\0"))
        else:
            dst = f_cp949_print(dst, arg)

    return dst


def f_sprintf(dst, *args):
    ret = EUDVariable()
    if EUDIf()(f_is116()):
        ret << f_cp949_print(dst, *args)
    if EUDElse()():
        ret << f_utf8_print(dst, *args)
    EUDEndIf()
    return ret


def f_addText(*args):
    f_cpprint(*args)


bufferepd = EUDVariable()


def f_makeText(*args):
    f_getcurpl()
    VProc(bufferepd, [bufferepd.QueueAssignTo(EPD(CP))])
    f_addText(*args)


def f_displayText():
    f_setcachedcp()
    DoActions(DisplayText(strBuffer))


@EUDFunc
def f_displayTextP(player):
    DoActions([SetMemory(0x6509B0, SetTo, player), DisplayText(strBuffer)])
    f_setcachedcp()


@EUDFunc
def f_displayTextAll():
    f_setlocalcp()
    VProc(_curpl_var, [_curpl_var.QueueAssignTo(EPD(CP)), DisplayText(strBuffer)])


def f_print(*args):
    f_makeText(*args)
    f_displayText()


def f_printP(player, *args):
    f_makeText(*args)
    f_displayTextP(player)


def f_printAll(*args):
    f_makeText(*args)
    f_displayTextAll()


def _CGFW(exprf, retn):
    rets = [ExprProxy(None) for _ in range(retn)]

    def _():
        vals = exprf()
        for ret, val in zip(rets, vals):
            ret._value = val

    EUDOnStart(_)
    return rets


soundBuffer = _CGFW(lambda: [GetStringIndex("_" * 64)], 1)[0]
soundBufferptr = EUDVariable()


def f_playSound(*args):
    f_sprintf(soundBufferptr, *args)
    DoActions(PlayWAV(soundBuffer))


def f_playSoundP(player, *args):
    f_getcurpl()
    DoActions(SetMemory(0x6509B0, SetTo, player))
    f_playSound(*args)
    f_setcachedcp()


def f_playSoundAll(*args):
    f_getcurpl()
    f_setlocalcp()
    f_playSound(*args)
    f_setcachedcp()


STRptr, STRepd = EUDCreateVariables(2)
add_STRptr, add_STRepd, write_bufferptr, write_bufferepd, reset_buffer = [
    Forward() for _ in range(5)
]


@EUDFunc
def f_strptr(strID):  # getStringPtr
    r, m = f_div(strID, 2)
    RawTrigger(actions=add_STRepd << r.AddNumber(0))
    ret = f_wread_epd(r, m * 2)  # strTable_epd + r
    RawTrigger(actions=add_STRptr << ret.AddNumber(0))
    EUDReturn(ret)  # strTable_ptr + strOffset


def f_init():
    SetVariables([STRptr, STRepd], f_dwepdread_epd(EPD(0x5993D4)))
    DoActions(
        [
            cp.SetNumber(f_dwread_epd(EPD(0x57F1B0))),
            SetMemory(add_STRptr + 20, SetTo, STRptr),
            SetMemory(add_STRepd + 20, SetTo, STRepd),
        ]
    )
    newptr = f_strptr(1)  # STRptr + newptr
    newepd = EPD(newptr)
    DoActions(
        [
            SetMemory(write_bufferptr + 20, SetTo, newptr),
            SetMemory(write_bufferepd + 20, SetTo, newepd),
            bufferepd.SetNumber(newepd),
            soundBufferptr.SetNumber(newptr),
        ]
    )
    f_reset()  # prevent Forward Not initialized
    _never = Forward()
    EUDJump(_never)
    reset_buffer << RawTrigger(
        actions=[
            write_bufferptr << ptr.SetNumber(0),
            write_bufferepd << epd.SetNumber(0),
        ]
    )
    f_TBLinit()
    _never << NextTrigger()


EUDOnStart(f_init)
chatptr, chatepd = EUDCreateVariables(2)


def f_reset():  # ptr, epd를 스트링 시작 주소로 설정합니다.
    _next = Forward()
    RawTrigger(nextptr=reset_buffer, actions=SetNextPtr(reset_buffer, _next))
    _next << NextTrigger()


NEXT_PTR = 0x628438
_restorePtr = Forward()
_nextptrcacheMatchCond = Forward()


@EUDFunc
def _updatenextptrcache():
    DoActions([
        SetMemory(_restorePtr + 20, SetTo, 0x59CCA8),
        SetMemory(_nextptrcacheMatchCond + 8, SetTo, 0x59CCA8)
    ])
    for i in range(10, -1, -1):
        RawTrigger(
            conditions=Memory(NEXT_PTR, AtLeast, 0x59CCA8 + 336 * 2 ** i),
            actions=[
                SetMemory(NEXT_PTR, Subtract, 336 * 2 ** i),
                SetMemory(_restorePtr + 20, Add, 336 * 2 ** i),
                SetMemory(_nextptrcacheMatchCond + 8, Add, 336 * 2 ** i),
            ],
        )


@EUDTypedFunc([TrgPlayer])
def f_printError(player):
    if EUDIfNot()([_nextptrcacheMatchCond << Memory(NEXT_PTR, Exactly, 0)]):
        _updatenextptrcache()
    EUDEndIf()
    DoActions(
        [
            SetMemory(NEXT_PTR, SetTo, 0),
            CreateUnit(1, 0, 1, player),
            _restorePtr << SetMemory(NEXT_PTR, SetTo, 0),
        ]
    )


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
def f_char_addstr(dstp, src):
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


def f_char_addbyte(dstp, b):
    while len(b) % 4 >= 1:
        b = b + b"\x0D"
    DoActions([[SetMemoryEPD(dstp, SetTo, b2i4(b[i:i + 4])), dstp.AddNumber(1)] for i in range(0, len(b), 4)])
    return dstp


def f_char_strbyte(dstp, s, encoding="UTF-8"):
    b = s.encode(encoding)
    return f_char_addbyte(dstp, b)


def f_char_add1c(dstp, s, encoding="UTF-8"):
    string = ""
    color = ""
    for i, c in enumerate(s):
        c_ = c.encode(encoding)
        ci = f_b2i(c_)
        if ci >= 0x01 and ci <= 0x1F and ci != 0x12 and ci != 0x13:
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

    return f_char_strbyte(dstp, string, encoding)


@EUDFunc
def f_char_addw(dstp, number):
    skipper = [Forward() for _ in range(9)]
    ch = [0] * 10

    for i in range(10):  # Get digits
        number, ch[i] = f_div(number, 10)
        if i != 9:
            EUDJumpIf(number == 0, skipper[i])

    for i in range(9, -1, -1):  # print digits
        if i != 9:
            skipper[i] << NextTrigger()
        f_dwwrite_epd(dstp, ch[i] + b"0"[0] + 0xD0D0D00)
        dstp += 1

    return dstp


@EUDFunc
def f_char_addptr(dstp, number):
    ch = [0] * 8
    for i in range(8):
        number, ch[i] = f_div(number, 16)

    for i in range(7, -1, -1):
        if EUDIf()(ch[i] <= 9):
            f_dwwrite_epd(dstp, ch[i] + b"0"[0] + 0xD0D0D00)
        if EUDElse()():
            f_dwwrite_epd(dstp, ch[i] + (b"A"[0] - 10) + 0xD0D0D00)
        EUDEndIf()
        dstp += 1

    return dstp


def f_cp949_charprint(dstp, *args):
    arg = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, f_str):
            dstp = f_char_addstr(dstp, arg._value)
        elif isUnproxyInstance(arg, f_1c):
            dstp = f_char_add1c(dstp, arg._value, encoding="cp949")
        elif isUnproxyInstance(arg, f_get):
            SetVariables(arg._value, dstp)
        elif isUnproxyInstance(arg, bytes):
            dstp = f_char_addbyte(dstp, arg)
        elif isUnproxyInstance(arg, str):
            dstp = f_char_strbyte(dstp, arg, encoding="cp949")
        elif isUnproxyInstance(arg, DBString):
            dstp = f_char_addstr(dstp, arg.GetStringMemoryAddr())
        elif isUnproxyInstance(arg, int):
            dstp = f_char_addstr(dstp, Db(u2b(str(arg & 0xFFFFFFFF)) + b"\0"))
        elif isUnproxyInstance(arg, EUDVariable) or IsConstExpr(arg):
            dstp = f_char_adddw(dstp, arg)
        elif isUnproxyInstance(arg, hptr):
            dstp = f_char_addptr(dstp, arg._value)
        else:
            raise EPError("unknown parameter type %s given to print_epd." % type(arg))
    f_dwwrite_epd(dstp, 0)
    return dstp


def f_utf8_charprint(dstp, *args):
    arg = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, str):
            dstp = f_char_strbyte(dstp, arg)
        elif isUnproxyInstance(arg, f_s2u):
            dstp = f_cp949_to_utf8_cpy_epd(dstp, arg._value)
        elif isUnproxyInstance(arg, f_1c):
            dstp = f_char_add1c(dstp, arg._value)
        else:
            dstp = f_cp949_charprint(dstp, arg)
    f_dwwrite_epd(dstp, 0)
    return dstp


def f_sprintf_epd(dstp, *args):
    ret = EUDVariable()
    if EUDIf()(f_is116()):
        ret << f_cp949_charprint(dstp, *args)
    if EUDElse()():
        ret << f_utf8_charprint(dstp, *args)
    EUDEndIf()

    return ret


def f_byteTest(s, e="UTF-8"):
    s = s.encode(e)
    while len(s) % 4 >= 1:
        s += b"\x00"
    for i in range(math.ceil(len(s) / 4)):
        print("{}: {}".format(i, s[4 * i : min([4 * (i + 1), len(s)])]))


def f_addText_epd(*args):
    epd << f_sprintf_epd(epd, *args)


def f_makeText_epd(*args):
    f_reset()
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
def f_dbstr_addstr2_epd(dst, epd):
    b = EUDVariable()
    br1.seekepd(epd)
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
        bw1.writebyte(ch[i] + b"0"[0])
        dst += 1
    bw1.flushdword()
    return dst


def f_dbstr_print2(dst, length, *args):
    if isinstance(dst, DBString):
        dst = dst.GetStringMemoryAddr()

    args = FlattenList(args)
    for arg in args:
        if isUnproxyInstance(arg, bytes):
            dst = f_dbstr_addstr2(dst, Db(arg + b"\0"))
        elif isUnproxyInstance(arg, str):
            dst = f_dbstr_addstr2(dst, Db(u2b(arg) + b"\0"))
        elif isUnproxyInstance(arg, DBString):
            dst = f_dbstr_addstr2(dst, arg.GetStringMemoryAddr())
        elif isUnproxyInstance(arg, int):
            dst = f_dbstr_addstr2(dst, Db(u2b(str(arg & 0xFFFFFFFF)) + b"\0"))
        elif isUnproxyInstance(arg, EUDVariable) or IsConstExpr(arg):
            dst = f_dbstr_adddw2(dst, arg, length)
        elif isUnproxyInstance(arg, f_str):
            dst = f_dbstr_addstr2(dst, arg._value)
        elif isUnproxyInstance(arg, f_strepd):
            dst = f_dbstr_addstr2_epd(dst, arg._value)
        else:
            dst = f_cp949_print(dst, arg)

    return dst


TBL_ptr, TBL_epd = EUDCreateVariables(2)
AddTBL_ptr, AddTBL_epd = Forward(), Forward()
_initTbl = EUDLightVariable(0)
_tbl_start, _tbl_end, _tbl_return = [Forward() for _ in range(3)]


@EUDFunc
def f_tblptr(tblID):
    r, m = f_div(tblID, 2)
    RawTrigger(actions=AddTBL_epd << r.AddNumber(0))
    ret = f_wread_epd(r, m * 2)  # strTable_epd + r
    RawTrigger(actions=AddTBL_ptr << ret.AddNumber(0))
    return ret  # tbl_ptr + tblOffset


def f_TBLinit():
    _tbl_start << NextTrigger()
    SetVariables([TBL_ptr, TBL_epd], f_dwepdread_epd(EPD(0x6D5A30)))
    DoActions(
        [
            SetMemory(AddTBL_epd + 20, SetTo, TBL_epd),
            SetMemory(AddTBL_ptr + 20, SetTo, TBL_ptr),
        ]
    )

    f_tblptr(0)  # prevent Forward Not initialized
    _tbl_end << RawTrigger(
        actions=[_initTbl.SetNumber(1), _tbl_return << SetNextPtr(0xEDAC, 0xF001)]
    )


def f_setTbl(tblID, offset, length, *args):
    _is_tbl_init, _next = Forward(), Forward()
    _is_tbl_init << RawTrigger(
        conditions=_initTbl.Exactly(0),
        actions=[
            SetNextPtr(_is_tbl_init, _tbl_start),
            SetNextPtr(_tbl_end, _next),
            SetMemory(_tbl_return + 16, SetTo, EPD(_is_tbl_init + 4)),
            SetMemory(_tbl_return + 20, SetTo, _next),
        ],
    )
    _next << NextTrigger()
    dst = f_tblptr(tblID) + offset
    f_dbstr_print2(dst, length, *args)


# legacy
colorArray = Color
f_getTblPtr = f_tblptr
f_ct_print = f_utf8_print
f_ct_print_epd = f_utf8_charprint
f_cprint = f_sprintf
f_cprint_epd = f_sprintf_epd
f_getoldcp = f_getcurpl
f_setoldcp = f_setcachedcp


def f_chatAnnouncement(*args):
    f_chatprint(12, *args)


def f_chatAnnouncement_epd(*args):
    f_chatprint_epd(12, *args)
