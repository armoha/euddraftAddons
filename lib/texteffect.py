from eudplib import *
import atexit
import customText4 as ct
import re
from itertools import combinations_with_replacement, cycle
'''
texteffect.py 0.2.0

0.1.0 - inital release.
0.2.0 - corrected issue: fixed-line display doesn't remove previous text.
        return 0 when effect is over, return 1 when effect is ongoing.
'''

TICK = EPD(0x57F23C)

timers = dict()
intervals = dict()
effect_keys = set()
reset_keys = set()
cts = dict()
alert_manual_reset = set()
identifiers = [
    u2b(2 * (c[0] + c[1]))
    for c in combinations_with_replacement(
        [
            "\x02", "\x03", "\x04", "\x06",
            "\x07", "\x08", "\x0D", "\x0E", "\x0F",
            "\x10", "\x11", "\x15", "\x16", "\x17",
            "\x18", "\x19", "\x1A", "\x1B", "\x1C",
            "\x1D", "\x1E", "\x1F"
        ], 2)
]
identifier_gen = cycle(identifiers)
start = EUDVariable()


@EUDFunc
def f_start_to_ct():
    global _set_to_ct
    _set_to_ct = Forward()
    DoActions(_set_to_ct << start.SetNumber(0xBABE))
    ct.f_reset()


def _init():
    f_start_to_ct()
    DoActions(SetMemory(_set_to_ct + 20, SetTo, ct.epd + 2))


EUDOnStart(_init)


def process_args_for_ct(*args):
    ct_args = tuple(ct.f_1c(x) if isUnproxyInstance(x, str)
                    else x for x in args)
    return ct_args


@EUDFunc
def f_write_identifier(identifier):
    DoActions([
        SetMemoryEPD(ct.epd, SetTo, identifier),
        SetMemoryEPD(ct.epd + 1, SetTo, identifier),
        ct.epd.AddNumber(2)
    ])


def f_reset(*args):
    key = str(args)
    reset_keys.add(key)
    if key not in timers:
        timers[key] = EUDVariable()
        intervals[key] = EUDLightVariable()
    _timer, _interval = timers[key], intervals[key]

    _timer << 0
    _interval << 0


txtPtr = EUDVariable()
display_text = EUDLightVariable()
restore_txtPtr = EUDLightVariable()


@EUDFunc
def f_update_txtPtr():
    once_per_tick = Forward()
    if EUDIf()(once_per_tick << MemoryEPD(TICK, AtLeast, 0)):
        txtPtr << f_dwread_epd(EPD(0x640B58))
        DoActions(SetMemory(once_per_tick + 8, SetTo, f_dwread_epd(TICK) + 1))
    EUDEndIf()


@EUDFunc
def f_floorTxtPtr(line):
    f_dwadd_epd(EPD(0x640B58), line)
    RawTrigger(
        conditions=Memory(0x640B58, AtLeast, 11),
        actions=SetMemory(0x640B58, Subtract, 11)
    )


@EUDFunc
def f_display():
    global txtPtr
    if EUDIf()(display_text == 1):
        ct.f_displayText()
        if EUDIf()(restore_txtPtr == 1):
            f_dwwrite_epd(EPD(0x640B58), txtPtr)
        if EUDElse()():
            txtPtr = f_dwread_epd(EPD(0x640B58))
        EUDEndIf()
    EUDEndIf()


@EUDFunc
def f_setTxtPtr(line, identifier1, identifier2):
    prev = f_dwread_cp(0)
    dst = ct.f_chatepd(prev)
    f_start_to_ct()
    if EUDIf()(prev % 2 == 0):
        if EUDIf()(MemoryEPD(dst, Exactly, identifier1)):
            f_dwwrite_epd(dst, 0)
        EUDEndIf()
    if EUDElseIf()(
        EUDSCAnd()
                (MemoryEPD(dst, AtMost, identifier2 + 0xFFFF))
                (MemoryEPD(dst, AtLeast, identifier2))()
    ):
        f_dwwrite_epd(dst, 0)
    EUDEndIf()
    f_floorTxtPtr(line)
    f_dwwrite_cp(0, f_dwread_epd(EPD(0x640B58)))


@EUDFunc
def f_setToErrorLine():
    ct.f_printError(EncodePlayer(CurrentPlayer))
    DoActions([
        display_text.SetNumber(0),
        ct.epd.SetNumber(ct.f_chatepd(12)),
        start.SetNumber(ct.f_chatepd(12) + 2),
    ])


@EUDFunc
def f_setPrevTxtPtr(identifier1, identifier2):
    prev = f_dwread_cp(0)
    dst = ct.f_chatepd(prev)
    f_start_to_ct()
    if EUDIf()(prev % 2 == 0):
        if EUDIf()(MemoryEPD(dst, Exactly, identifier1)):
            DoActions(SetMemory(0x640B58, SetTo, prev))
            EUDReturn()
        EUDEndIf()
    if EUDElseIf()(
        EUDSCAnd()
                (MemoryEPD(dst, AtMost, identifier2 + 0xFFFF))
                (MemoryEPD(dst, AtLeast, identifier2))()
    ):
        DoActions(SetMemory(0x640B58, SetTo, prev))
        EUDReturn()
    EUDEndIf()
    f_dwwrite_cp(0, f_dwread_epd(EPD(0x640B58)))
    restore_txtPtr << 0


def f_effectBase(*args, line=0, autoreset=True, timer=None):
    f_update_txtPtr()
    identifier = ct.b2i(next(identifier_gen))
    i2 = identifier - (identifier % 0x10000)
    display_text << 1
    restore_txtPtr << 1

    if timer is None:
        key = str(args)
        if re.search(r'<\S* object at 0x[0-9A-F]+>', key) is not None:
            raise Exception(
                "object가 인자로 쓰이면 timer를 지정해야합니다; Must assign timer when arguments have object: {}".format(args))
    else:
        key = str((timer,))

    if autoreset is True:  # enable auto-reset timer
        check_tick = Forward()
        if EUDIf()(check_tick << MemoryEPD(TICK, AtLeast, 0)):
            if timer is None:
                f_reset(*args)
            else:
                f_reset(timer)
            DoActions(SetMemory(check_tick + 8, SetTo, f_dwread_epd(TICK) + 1))
        EUDEndIf()
        DoActions(SetMemory(check_tick + 8, Add, 1))
    else:
        alert_manual_reset.add(key)

    effect_keys.add(key)
    if key not in timers:
        timers[key] = EUDVariable()
        intervals[key] = EUDLightVariable()

    prev = EUDVariable()

    if isUnproxyInstance(line, EUDVariable):
        if EUDIf()(line == 12):
            prev << 12
            f_setToErrorLine()
        if EUDElse()():
            ct.f_getoldcp()
            f_setcurpl(EPD(prev.getValueAddr()))
            if EUDIf()(line <= 10):
                f_setTxtPtr(line, identifier, i2)
            if EUDElse()():
                f_setPrevTxtPtr(identifier, i2)
            EUDEndIf()
            ct.f_setoldcp()
        EUDEndIf()
    elif line == 12:
        f_setToErrorLine()
    else:
        ct.f_getoldcp()
        f_setcurpl(EPD(prev.getValueAddr()))
        if line >= 0 and line <= 10:
            f_setTxtPtr(line, identifier, i2)
        else:
            f_setPrevTxtPtr(identifier, i2)
        ct.f_setoldcp()

    f_write_identifier(identifier)
    ct_args = process_args_for_ct(*args)
    ct_key = str(ct_args)
    if ct_key not in cts:

        @EUDFunc
        def f_write_ct_str():
            ct.f_addText_epd(*ct_args)
            EUDReturn(ct.epd - start)

        cts[ct_key] = f_write_ct_str
    txtlen = cts[ct_key]()

    return txtlen


def f_fadein(*args, color=None, interval=1, line=0, autoreset=True, timer=None):

    txtlen = f_effectBase(*args, line=line, autoreset=autoreset, timer=timer)
    if color is None:
        color = (0x14, 0x05, 0x04, 0x03)

    if timer is None:
        key = str(args)
        if re.search(r'<\S* object at 0x[0-9A-F]+>', key) is not None:
            raise Exception(
                "object가 인자로 쓰이면 timer를 지정해야합니다; Must assign timer when arguments have object: {}".format(args))
    else:
        key = str((timer,))
    _timer, _interval = timers[key], intervals[key]

    ret = EUDVariable()

    if EUDIf()(_timer >= txtlen + len(color) - 2):
        ret << 0
    if EUDElse()():
        ret << 1
        for i, c in enumerate(color):
            if EUDIf()([_timer >= i, _timer <= txtlen + i - 1]):
                f_bwrite_epd(start + _timer - i, 3, c)
            EUDEndIf()
    EUDEndIf()

    _interval += 1
    RawTrigger(
        conditions=_interval.AtLeast(interval),
        actions=[
            _interval.SetNumber(0),
            _timer.AddNumber(1)
        ]
    )
    if EUDIf()(_timer >= txtlen + len(color) - 1):
        _timer -= 1
    EUDEndIf()

    f_display()

    return ret


def f_fadeout(*args, color=None, interval=1, line=0, autoreset=True, timer=None):

    txtlen = f_effectBase(*args, line=line, autoreset=autoreset, timer=timer)
    if color is None:
        color = (0x14, 0x05, 0x04, 0x03)

    if timer is None:
        key = str(args)
        if re.search(r'<\S* object at 0x[0-9A-F]+>', key) is not None:
            raise Exception(
                "object가 인자로 쓰이면 timer를 지정해야합니다; Must assign timer when arguments have object: {}".format(args))
    else:
        key = str((timer,))
    _timer, _interval = timers[key], intervals[key]

    ret = EUDVariable()

    if EUDIf()(_timer >= txtlen + len(color) - 2):
        ret << 0
    if EUDElse()():
        ret << 1
    EUDEndIf()

    if EUDIf()(_timer >= 1):
        s = txtlen + len(color) - 2 - _timer
        for i, c in enumerate(color):
            if EUDIf()([s >= i, s <= txtlen + i - 1]):
                f_bwrite_epd(start + s - i, 3, c)
            EUDEndIf()
    EUDEndIf()

    _interval += 1
    RawTrigger(
        conditions=_interval.AtLeast(interval),
        actions=[
            _interval.SetNumber(0),
            _timer.AddNumber(1)
        ]
    )
    if EUDIf()(_timer >= txtlen + len(color) - 1):
        _timer -= 1
    EUDEndIf()

    f_display()

    return ret


def _warning():
    for key in timers:
        if key not in effect_keys:
            raise Exception(
                "미사용 타이머를 reset했습니다; reset unused timer: {}".format(key))
        if key not in reset_keys and key in alert_manual_reset:
            raise Exception(
                "수동 reset 필요; need manual reset for timer: {}".format(key))


atexit.register(_warning)
