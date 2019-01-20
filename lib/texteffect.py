import itertools

import customText as ct
import eudplib.eudlib.stringf.cputf8 as cputf
from customText import cw
from eudplib import *
from eudplib.eudlib.stringf.rwcommon import br1

"""
texteffect.py 0.3.4 by Artanis

## [0.3.4] - 2019-01-18
### Fixed
- f_fadein, f_fadeout used (arg,) as timer when len(args) == 1.
- Now use MemoryX and SetDeathsX from eudx.py or euddraft 0.8.3.0+.
- f_fadein, f_fadeout issued error with color code(s) and no content.

## [0.3.2] - 2018-12-12
### Changed
- Now use customText 0.4.0
### Added
- cp949 option for stat_txt.tbl modification
- s2u option for concatenate unit name

## [0.3.1] - 2018-12-03
### Fixed
- Fix keep running f_fadeout(line=12) crash SC

## [0.3.0] - 2018-12-03
### A complete code rewrite for customText4 0.3.2
### Changed
- Change named argument's name of f_fadein, f_fadeout as followings
    interval -> wait
    autoreset -> reset
- Text identifier and timer are now identical
    - Can remove text on screen by f_remove(timer), effects sharing timer uses same identifier.

### Added
- f_char_cpprint and series of CurrentPlayer print functions are added.
- Add f_settimer(timer, Modifier, Value)

### Removed
- ct.f_get is unsupported for now.

0.2.1 - reduce trigger amount. increase identifiers from 253 to 113379904.
0.2.0 - corrected issue: fixed-line display doesn't remove previous text.
        return 0 when effect is over, return 1 when effect is ongoing.
0.1.0 - inital release.
"""

try:
    MemoryX
except (NameError):
    from eudx import MemoryX, SetDeathsX

CP = 0x6509B0
color_codes = list(range(1, 32))
color_codes.remove(0x12)  # right align
color_codes.remove(0x13)  # center align
color_code = b"\x02"
color_v = EUDVariable()


@EUDFunc
def f_char_cp949_to_utf8_cp(src):
    br1.seekoffset(src)

    if EUDInfLoop()():
        b1 = br1.readbyte()
        EUDBreakIf(b1 == 0)
        if EUDIf()(b1 < 128):
            cw.writebyte(color_v)
            cw.writebyte(b1)
            cw.flushdword()
            dst += 1
        if EUDElse()():
            b2 = br1.readbyte()
            EUDBreakIf(b2 == 0)
            code = cputf.cvtb[b2 * 256 + b1]
            if EUDIf()(code <= 0x07FF):  # Encode as 2-byte
                cw.writebyte(color_v)
                cw.writebyte(0b11000000 | (code // (1 << 6)) & 0b11111)
                cw.writebyte(0b10000000 | (code // (1 << 0)) & 0b111111)
                cw.flushdword()
                dst += 2
            if EUDElse()():  # Encode as 3-byte
                cw.writebyte(color_v)
                cw.writebyte(0b11100000 | (code // (1 << 12)) & 0b1111)
                cw.writebyte(0b10000000 | (code // (1 << 6)) & 0b111111)
                cw.writebyte(0b10000000 | (code // (1 << 0)) & 0b111111)
                dst += 3
            EUDEndIf()
        EUDEndIf()
    EUDEndInfLoop()


@EUDFunc
def f_char_addstr_cp(src):
    if EUDInfLoop()():
        b1 = br1.readbyte()
        EUDBreakIf(b1 == 0)
        cw.writebyte(color_v)
        cw.writebyte(b1)
        if EUDIf()(b1 <= 0x7F):
            cw.flushdword()
        if EUDElse()():
            b2 = br1.readbyte()
            cw.writebyte(b2)
            if EUDIf()(b1 <= 0xDF):  # Encode as 2-byte
                cw.flushdword()
            if EUDElse()():  # 3-byte
                cw.writebyte(br1.readbyte())
            EUDEndIf()
        EUDEndIf()
    EUDEndInfLoop()


@EUDFunc
def f_char_adddw_cp(number):
    skipper = [Forward() for _ in range(9)]
    ch = [0] * 10

    for i in range(10):  # Get digits
        number, ch[i] = f_div(number, 10)
        if i != 9:
            EUDJumpIf(number == 0, skipper[i])

    for i in range(9, -1, -1):  # print digits
        if i != 9:
            skipper[i] << NextTrigger()
        DoActions(
            [
                SetDeaths(
                    CurrentPlayer, SetTo, color_v + ch[i] * 256 + (0x0D0D3000), 0
                ),
                SetMemory(CP, Add, 1),
            ]
        )


def f_char_cpprint(*args):
    global color_code
    args = FlattenList(args)
    for arg in args:
        bf = u2utf8
        if isUnproxyInstance(arg, ct.f_cp949):
            bf = u2b
            arg = arg._value
        if isinstance(arg, str):
            bytestring = b""
            for char in arg:
                char = bf(char)
                if ct.f_b2i(char) in color_codes:
                    color_code = char
                    continue
                while len(char) < 3:
                    char = char + b"\x0D"
                bytestring = bytestring + color_code + char
            DoActions(color_v.SetNumber(b2i1(color_code)))
            if not bytestring:
                bytestring = color_code + b"\x0D\x0D\x0D"
            ct.f_cpprint(bytestring)
        elif isUnproxyInstance(arg, ct.f_str):
            br1.seekoffset(arg._value)
            f_char_addstr_cp(arg._value)
        elif isUnproxyInstance(arg, ct.f_s2u):
            f_char_cp949_to_utf8_cp(arg._value)
        elif isUnproxyInstance(arg, ct.f_strepd):
            br1.seekepd(arg._value)
            f_addstr_cp_epd(arg._value)
        elif isUnproxyInstance(arg, EUDVariable) or IsConstExpr(arg):
            f_char_adddw_cp(arg)
        else:
            ct.f_cpprint(arg)
    DoActions(SetDeaths(CurrentPlayer, SetTo, 0, 0))


def f_charaddText(*args):
    f_char_cpprint(*args)


def f_charmakeText(*args):
    global color_code
    color_code = b"\x02"
    ct.f_updatecpcache()
    DoActions(color_v.SetNumber(2))
    VProc(ct.bufferepd, ct.bufferepd.QueueAssignTo(EPD(CP)))
    f_charaddText(*args)


def f_charprint(*args):
    f_charmakeText(*args)
    ct.f_displayText()


def _init():
    global _cpbelowbuffer, _isbelowbuffer
    _cpbelowbuffer = EUDVariable()
    _checkcp, _checkSTR = Forward(), Forward()
    _isbelowbuffer = RawTrigger(
        conditions=[
            _checkcp << Memory(CP, AtMost, 1),
            _checkSTR << Memory(CP, AtLeast, 0)
        ],
        actions=_cpbelowbuffer.SetNumber(1),
    )
    ct.f_reset()
    DoActions(
        [
            SetMemory(_checkcp + 8, Add, ct.epd),
            SetMemory(_checkSTR + 8, SetTo, ct.STRepd),
            [SetMemory(0x640B60 + 436 * i, SetTo, 0) for i in range(7)],
            [SetMemory(0x640C3C + 436 * i, SetTo, 0) for i in range(5)],
        ]
    )


EUDOnStart(_init)
timer_dict, counter_dict, id_dict = dict(), dict(), dict()
GAMETICK = 0x57F23C
TXTPTR = 0x640B58
id_codes = "\x02\x03\x04\x06\x07\x08\x0D\x0E\x0F\x10\x11\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F"
id_gen = itertools.cycle(itertools.product(id_codes, repeat=4))


def makeeffectText(ids, *args):
    global color_code
    color_code = b"\x02"
    ct.f_updatecpcache()
    DoActions(color_v.SetNumber(2))
    VProc(ct.bufferepd, ct.bufferepd.QueueAssignTo(EPD(CP)))
    ct.f_cpprint(ids + ids)
    f_charaddText(*args)


def printEffectOnErrorline(ids, *args):
    global color_code
    color_code = b"\x04"
    ct.f_updatecpcache()
    ct.f_printError(CurrentPlayer)
    DoActions(
        [
            color_v.SetNumber(4),
            SetMemory(0x640B60 + 218 * 12, SetTo, 0),
            SetMemory(CP, SetTo, EPD(0x640B60 + 218 * 12)),
        ]
    )
    ct.f_cpprint(ids + ids)
    f_charaddText(*args)


def add_timer(timer):
    if timer not in timer_dict:
        timer_dict[timer] = EUDVariable()
        counter_dict[timer] = EUDLightVariable()
        id_dict[timer] = "".join(next(id_gen))


@EUDFunc
def _remove(id1, id2):
    txtPtr = EUDVariable()
    odd, even = [Forward() for _ in range(7)], [Forward() for _ in range(5)]
    DoActions(
        [
            txtPtr.SetNumber(-1),
            [SetMemory(odd[i] + 8, SetTo, id1) for i in range(7)],
            [SetMemory(even[i] + 8, SetTo, id2) for i in range(5)],
        ]
    )
    for i in range(7):
        _odd = 0x640B60 + 436 * i
        RawTrigger(
            conditions=[odd[i] << Memory(_odd, Exactly, -1)],
            actions=[txtPtr.SetNumber(2 * i), SetMemory(_odd, SetTo, 0)],
        )
    for i in range(5):
        _even = 0x640C3C + 436 * i
        RawTrigger(
            conditions=[
                MemoryX(_even - 4, AtLeast, 1, 0xFF0000),
                even[i] << Memory(_even, Exactly, -1),
            ],
            actions=[txtPtr.SetNumber(2 * i + 1), SetMemory(_even, SetTo, 0)],
        )
    return txtPtr


def f_remove(timer):
    add_timer(timer)
    id1 = id_dict[timer]
    id2 = id1[2:4] + id1[0:2]
    id1, id2 = b2i4(u2b(id1)), b2i4(u2b(id2))
    return _remove(id1, id2)


@EUDFunc
def update_gametick_cache():
    global gametick_cache
    gametick_cache = EUDVariable()
    gametick_match = Forward()
    if EUDIfNot()([gametick_match << Memory(GAMETICK, Exactly, 0)]):
        DoActions(gametick_cache.SetNumber(0))
        for i in range(31, -1, -1):
            RawTrigger(
                conditions=Memory(GAMETICK, AtLeast, 2 ** i),
                actions=[
                    SetMemory(GAMETICK, Subtract, 2 ** i),
                    gametick_cache.AddNumber(2 ** i),
                ],
            )
        DoActions(
            [
                SetMemory(gametick_match + 8, SetTo, gametick_cache),
                SetMemory(GAMETICK, SetTo, gametick_cache),
            ]
        )
    EUDEndIf()


def is_cp_below_strBuffer(actions):
    _next = Forward()
    RawTrigger(
        nextptr=_isbelowbuffer,
        actions=[actions]
        + [_cpbelowbuffer.SetNumber(0), SetNextPtr(_isbelowbuffer, _next)],
    )
    _next << NextTrigger()


def R2L(color, timer, color_dict={}):
    try:
        _f = color_dict[color]
    except (KeyError):

        @EUDFunc
        def _f(timer):
            _jump, _isend, _end = [Forward() for _ in range(3)]
            ret = EUDVariable()
            is_cp_below_strBuffer([ret.SetNumber(1), SetNextPtr(_isend, _jump)])
            _isend << RawTrigger(
                conditions=_cpbelowbuffer.Exactly(1),
                actions=[ret.SetNumber(0), SetNextPtr(_isend, _end)],
            )
            _jump << NextTrigger()
            for c in reversed(color):
                is_cp_below_strBuffer([])
                RawTrigger(
                    conditions=_cpbelowbuffer.Exactly(0),
                    actions=[
                        SetDeathsX(CurrentPlayer, SetTo, c, 0, 0xFF),
                        SetMemory(CP, Subtract, 1),
                    ],
                )
            _end << NextTrigger()
            return ret

        color_dict[color] = _f
    return _f(timer)


def f_settimer(timer, modtype, value):
    add_timer(timer)
    DoActions(SetMemory(timer_dict[timer].getValueAddr(), modtype, value))


def f_reset(timer):
    f_settimer(timer, SetTo, 0)


prevTxtPtr = EUDVariable()


@EUDFunc
def f_update_txtptr():
    _once_per_gametick, _txtptr_match = [Forward(), Forward()], Forward()
    if EUDIfNot()(
        [
            _once_per_gametick[0] << Memory(GAMETICK, AtMost, 0),
            _txtptr_match << Memory(TXTPTR, Exactly, 0),
        ]
    ):
        if EUDIf()([_once_per_gametick[1] << Memory(GAMETICK, Exactly, 0)]):
            DoActions(
                [
                    prevTxtPtr.SetNumber(0),
                    [SetMemory(_once_per_gametick[i] + 8, Add, 1) for i in range(2)],
                ]
            )
        if EUDElse()():
            update_gametick_cache()
            VProc(
                gametick_cache,
                [
                    prevTxtPtr.SetNumber(0),
                    gametick_cache.QueueAssignTo(EPD(_once_per_gametick[0]) + 2),
                ],
            )
            VProc(
                gametick_cache,
                [
                    SetMemory(_once_per_gametick[1] + 8, SetTo, 1),
                    gametick_cache.QueueAddTo(EPD(_once_per_gametick[1]) + 2),
                ],
            )
        EUDEndIf()
        for i in range(3, -1, -1):
            RawTrigger(
                conditions=Memory(TXTPTR, AtLeast, 2 ** i),
                actions=[
                    SetMemory(TXTPTR, Subtract, 2 ** i),
                    prevTxtPtr.AddNumber(2 ** i),
                ],
            )
        DoActions(
            [
                SetMemory(_txtptr_match + 8, SetTo, prevTxtPtr),
                SetMemory(TXTPTR, SetTo, prevTxtPtr),
            ]
        )
    EUDEndIf()


CurrentPlayerOnly = True


def f_fadein(*args, color=None, wait=1, line=-1, reset=True, timer=None):
    """Print multiple string / number and apply color from Left To Right

    Keyword arguments:
    color -- tuple of color codes (default 0x03, 0x04, 0x05, 0x14)
    wait  -- time interval between effect (default 1)
    line  -- DisplayText on Fixed Line when (0~10 or EUDVariable),
            12: print on status line, -1: print as normal DisplayText (default -1)
    reset -- automatically reset when didn't run for a moment (default True)
    timer -- internal timer and identifier (default: vargs)
    """
    if color is None:
        color = (0x03, 0x04, 0x05, 0x14)
    if timer is None:
        if len(args) == 1:
            timer = args[0]
        else:
            timer = args
    key = timer
    add_timer(key)
    timer, counter, ids = timer_dict[key], counter_dict[key], id_dict[key]
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0) or line == -1:
        if CurrentPlayerOnly:
            EUDJumpIfNot(Memory(0x6509B0, Exactly, ct.cp), _end)
        makeeffectText(ids, *args)
        VProc(
            ct.bufferepd,
            [
                SetMemory(CP, SetTo, 3 - len(color)),
                ct.bufferepd.QueueAddTo(EPD(CP)),
            ],
        )
    elif line == 12:
        if CurrentPlayerOnly:
            EUDJumpIfNot(Memory(0x6509B0, Exactly, ct.cp), _end)
        printEffectOnErrorline(ids, *args)
        DoActions(SetMemory(CP, SetTo, EPD(0x640B60 + 218 * 12) + 3 - len(color)))
    else:
        DoActions(
            [
                color_v.SetNumber(2),
                SetMemory(CP, Add, 3 - len(color)),
            ]
        )
        ct.f_cpprint(ids + ids)
        f_charaddText(*args)
    if reset is True:
        check_gametick = Forward()
        if EUDIf()([check_gametick << Memory(GAMETICK, AtLeast, 0)]):
            update_gametick_cache()
            VProc(
                gametick_cache,
                [
                    timer.SetNumber(0),
                    SetMemory(check_gametick + 8, SetTo, 1),
                    gametick_cache.QueueAddTo(EPD(check_gametick) + 2),
                ],
            )
        EUDEndIf()
    _skip = [Forward() for _ in range(3)]
    ret = EUDVariable()
    VProc(timer, [
            timer.QueueAddTo(EPD(CP)),
            counter.AddNumber(1),
            [SetMemory(check_gametick + 8, Add, 1) if reset is True else []],
            ret.SetNumber(1),
            SetNextPtr(_skip[0], _skip[1]),
        ]
    )
    _skip[0] << RawTrigger(
        conditions=[
            Deaths(CurrentPlayer, Exactly, 0, 0),
            timer.AtLeast(2 + len(color))
        ],
        actions=[
            SetNextPtr(_skip[0], _skip[2]),
            ret.SetNumber(0),
            counter.SetNumber(0),
        ],
    )
    _skip[1] << RawTrigger(actions=SetMemory(CP, Add, len(color) - 1))
    R2L(color, timer)
    _skip[2] << RawTrigger(
        conditions=counter.AtLeast(max(wait, 1)),
        actions=[counter.SetNumber(0), timer.AddNumber(1)],
    )
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0):
        f_update_txtptr()
        f_remove(key)
        if line >= 1:
            DoActions(SetMemory(TXTPTR, Add, line))
            RawTrigger(
                conditions=Memory(TXTPTR, AtLeast, 11),
                actions=SetMemory(TXTPTR, Subtract, 11),
            )
    elif line == -1:
        displayedTxtPtr = f_remove(key)
        if EUDIf()(displayedTxtPtr <= 10):
            f_update_txtptr()
            DoActions(SetMemory(TXTPTR, SetTo, displayedTxtPtr))
        EUDEndIf()
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0) or line == -1:
        ct.f_displayText()
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0):
        VProc(prevTxtPtr, [prevTxtPtr.QueueAssignTo(EPD(TXTPTR))])
    elif line == -1:
        if EUDIf()(displayedTxtPtr <= 10):
            VProc(prevTxtPtr, [prevTxtPtr.QueueAssignTo(EPD(TXTPTR))])
        EUDEndIf()
    _end << NextTrigger()
    return ret


def f_fadeout(*args, color=None, wait=1, line=-1, reset=True, timer=None):
    """Print multiple string / number and apply color from Right To Left

    Keyword arguments:
    color -- tuple of color codes (default 0x03, 0x04, 0x05, 0x14)
    wait  -- time interval between effect (default 1)
    line  -- DisplayText on Fixed Line when (0~10 or EUDVariable),
            12: print on status line, -1: print as normal DisplayText (default -1)
    reset -- automatically reset when didn't run for a moment (default True)
    timer -- internal timer and identifier (default: vargs)
    """
    if color is None:
        color = (0x03, 0x04, 0x05, 0x14)
    if timer is None:
        if len(args) == 1:
            timer = args[0]
        else:
            timer = args
    key = timer
    add_timer(key)
    timer, counter, ids = timer_dict[key], counter_dict[key], id_dict[key]
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0) or line == -1:
        if CurrentPlayerOnly:
            EUDJumpIfNot(Memory(0x6509B0, Exactly, ct.cp), _end)
        makeeffectText(ids, *args)
    elif line == 12:
        if CurrentPlayerOnly:
            EUDJumpIfNot(Memory(0x6509B0, Exactly, ct.cp), _end)
        printEffectOnErrorline(ids, *args)
    else:
        DoActions(color_v.SetNumber(2))
        ct.f_cpprint(ids + ids)
        f_charaddText(*args)
    if reset is True:
        check_gametick = Forward()
        if EUDIf()([check_gametick << Memory(GAMETICK, AtLeast, 0)]):
            update_gametick_cache()
            VProc(
                gametick_cache,
                [
                    timer.SetNumber(0),
                    SetMemory(check_gametick + 8, SetTo, 1),
                    gametick_cache.QueueAddTo(EPD(check_gametick) + 2),
                ],
            )
        EUDEndIf()
    if isinstance(line, int) and line == 12:
        ret = EUDVariable()
        _skip = [Forward() for _ in range(3)]
    DoActions(
        [
            counter.AddNumber(1),
            SetMemory(CP, Add, len(color) - 1),
            SetMemory(CP, Subtract, timer),
            [SetMemory(check_gametick + 8, Add, 1) if reset is True else []],
            [ret.SetNumber(1), SetNextPtr(_skip[0], _skip[1])] if isinstance(line, int) and line == 12 else []
        ]
    )
    if isinstance(line, int) and line == 12:
        _skip[0] << RawTrigger(
            conditions=Memory(CP, AtMost, EPD(0x640B60 + 218 * 12) - 1),
            actions=[ret.SetNumber(0), SetNextPtr(_skip[0], _skip[2])]
        )
        _skip[1] << NextTrigger()
        R2L(color, timer)
    else:
        ret = R2L(color, timer)
    if isinstance(line, int) and line == 12:
        _skip[2] << NextTrigger()
    RawTrigger(conditions=ret.Exactly(0), actions=counter.SetNumber(0))
    RawTrigger(
        conditions=counter.AtLeast(max(wait, 1)),
        actions=[counter.SetNumber(0), timer.AddNumber(1)],
    )
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0):
        f_update_txtptr()
        f_remove(key)
        if line >= 1:
            DoActions(SetMemory(TXTPTR, Add, line))
            RawTrigger(
                conditions=Memory(TXTPTR, AtLeast, 11),
                actions=SetMemory(TXTPTR, Subtract, 11),
            )
    elif line == -1:
        displayedTxtPtr = f_remove(key)
        if EUDIf()(displayedTxtPtr <= 10):
            f_update_txtptr()
            DoActions(SetMemory(TXTPTR, SetTo, displayedTxtPtr))
        EUDEndIf()
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0) or line == -1:
        ct.f_displayText()
    if isinstance(line, EUDVariable) or (line <= 10 and line >= 0):
        VProc(prevTxtPtr, [prevTxtPtr.QueueAssignTo(EPD(TXTPTR))])
    elif line == -1:
        if EUDIf()(displayedTxtPtr <= 10):
            VProc(prevTxtPtr, [prevTxtPtr.QueueAssignTo(EPD(TXTPTR))])
        EUDEndIf()
    _end << NextTrigger()
    return ret
