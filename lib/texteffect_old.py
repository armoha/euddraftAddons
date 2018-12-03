import atexit
import itertools
import re

from eudplib import *

import customText4 as ct

'''
texteffect.py 0.2.1

0.2.1 - reduce trigger amount. increase identifiers from 253 to 113379904.
0.2.0 - corrected issue: fixed-line display doesn't remove previous text.
        return 0 when effect is over, return 1 when effect is ongoing.
0.1.0 - inital release.
'''

TICK = EPD(0x57F23C)

timers = dict()
intervals = dict()
effect_keys = set()
reset_keys = set()
cts = dict()
alert_manual_reset = set()
color_codes = "\x02\x03\x04\x06\x07\x08\x0D\x0E\x0F\x10\x11\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F"
identifiers = itertools.product(color_codes, repeat=6)
identifier_gen = itertools.cycle(identifiers)
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
odds_1, odds_2, even_1, even_2 = EUDCreateVariables(4)


def f_process_args_for_ct(*args):
    ct_args = tuple(ct.f_char(x) if isUnproxyInstance(x, str)
                    else x for x in args)
    return ct_args


@EUDFunc
def f_write_identifier():
    DoActions([
        SetMemoryEPD(ct.epd, SetTo, odds_1),
        SetMemoryEPD(ct.epd + 1, SetTo, odds_2),
        ct.epd.AddNumber(2)
    ])


def f_add_timer(key):
    if key not in timers:
        timers[key] = EUDVariable()
        intervals[key] = EUDLightVariable()


def f_reset(*args):
    key = str(args)
    reset_keys.add(key)
    f_add_timer(key)
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
def f_setTxtPtr(line):
    prev = f_dwread_cp(0)
    dst = ct.f_chatepd(prev)
    f_start_to_ct()
    if EUDIf()(prev % 2 == 0):
        if EUDIf()(EUDSCAnd()
                           (MemoryEPD(dst, Exactly, odds_1))
                           (MemoryEPD(dst, Exactly, odds_2))()
        ):
            f_dwwrite_epd(dst, 0)
        EUDEndIf()
    if EUDElseIf()(EUDSCAnd()
                           (MemoryEPD(dst, AtMost, even_1 + 0xFFFF))
                           (MemoryEPD(dst, AtLeast, even_1))
                           (MemoryEPD(dst, Exactly, even_2))()
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
def f_setPrevTxtPtr():
    prev = f_dwread_cp(0)
    dst = ct.f_chatepd(prev)
    f_start_to_ct()
    if EUDIf()(prev % 2 == 0):
        if EUDIf()(EUDSCAnd()
                           (MemoryEPD(dst, Exactly, odds_1))
                           (MemoryEPD(dst, Exactly, odds_2))()
        ):
            DoActions(SetMemory(0x640B58, SetTo, prev))
            EUDReturn()
        EUDEndIf()
    if EUDElseIf()(EUDSCAnd()
                           (MemoryEPD(dst, AtMost, even_1 + 0xFFFF))
                           (MemoryEPD(dst, AtLeast, even_1))
                           (MemoryEPD(dst, Exactly, even_2))()
    ):
        DoActions(SetMemory(0x640B58, SetTo, prev))
        EUDReturn()
    EUDEndIf()
    f_dwwrite_cp(0, f_dwread_epd(EPD(0x640B58)))
    restore_txtPtr << 0


def f_write_ct_str(*args):
    ct_args = f_process_args_for_ct(*args)
    ct_key = str(ct_args)
    if ct_key not in cts:

        @EUDFunc
        def _write_ct_str():
            ct.f_addText_epd(*ct_args)
            EUDReturn(ct.epd - start)

        cts[ct_key] = _write_ct_str
    txtlen = cts[ct_key]()

    return txtlen


def f_effectBase(*args, line=0, autoreset=True, timer=None):
    f_update_txtPtr()
    c0, c1, c2, c3, c4, c5 = next(identifier_gen)
    w1, w2, w3 = [ct.f_b2i(u2b(x)) for x in (c0 + c1, c2 + c3, c4 + c5)]
    SetVariables([odds_1, odds_2, even_1, even_2, display_text, restore_txtPtr],
                 [w1 + w2 * 0x10000, w3 + 0x0D0D * 0x10000,
                  w1 * 0x10000, w2 + w3 * 0x10000, 1, 1])

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
    f_add_timer(key)

    prev = EUDVariable()

    if isUnproxyInstance(line, EUDVariable):
        if EUDIf()(line == 12):
            prev << 12
            f_setToErrorLine()
        if EUDElse()():
            f_getcurpl()
            f_dwwrite_epd(EPD(0x6509B0), EPD(prev.getValueAddr()))
            if EUDIf()(line <= 10):
                f_setTxtPtr(line)
            if EUDElse()():
                f_setPrevTxtPtr()
            EUDEndIf()
            ct.f_setcachedcp()
        EUDEndIf()
    elif line == 12:
        f_setToErrorLine()
    else:
        f_getcurpl()
        f_dwwrite_epd(EPD(0x6509B0), EPD(prev.getValueAddr()))
        if line >= 0 and line <= 10:
            f_setTxtPtr(line)
        else:
            f_setPrevTxtPtr()
        ct.f_setcachedcp()

    f_write_identifier()
    txtlen = f_write_ct_str(*args)

    return txtlen


l2r, r2l = dict(), dict()


def f_l2r(color, _timer, txtlen):
    if color not in l2r:

        @EUDFunc
        def _l2r(_timer, txtlen):
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
            EUDReturn(ret)

        l2r[color] = _l2r
    return l2r[color](_timer, txtlen)


def f_fadein(*args, color=None, interval=1, line=0,
             autoreset=True, timer=None, txtlen=None):
    if txtlen is None:
        txtlen = f_effectBase(*args, line=line, autoreset=autoreset, timer=timer)
    elif txtlen is True:
        txtlen = f_write_ct_str(*args)

    if color is None:
        color = (0x14, 0x05, 0x04, 0x03)

    if timer is None:
        key = str(args)
        if re.search(r'<\S* object at 0x[0-9A-F]+>', key) is not None:
            raise Exception(
                "object가 인자로 쓰이면 timer를 지정해야합니다; Must assign timer when arguments have object: {}".format(args))
    else:
        key = str((timer,))

    f_add_timer(key)
    _timer, _interval = timers[key], intervals[key]

    ret = f_l2r(color, _timer, txtlen)

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


def f_r2l(color, _timer, txtlen):
    if color not in r2l:

        @EUDFunc
        def _r2l(_timer, txtlen):
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
            EUDReturn(ret)

        r2l[color] = _r2l
    return r2l[color](_timer, txtlen)


def f_fadeout(*args, color=None, interval=1, line=0,
              autoreset=True, timer=None, txtlen=None):
    if txtlen is None:
        txtlen = f_effectBase(*args, line=line, autoreset=autoreset, timer=timer)
    elif txtlen is True:
        txtlen = f_write_ct_str(*args)

    if color is None:
        color = (0x14, 0x05, 0x04, 0x03)

    if timer is None:
        key = str(args)
        if re.search(r'<\S* object at 0x[0-9A-F]+>', key) is not None:
            raise Exception(
                "object가 인자로 쓰이면 timer를 지정해야합니다; Must assign timer when arguments have object: {}".format(args))
    else:
        key = str((timer,))

    f_add_timer(key)
    _timer, _interval = timers[key], intervals[key]

    ret = f_r2l(color, _timer, txtlen)

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


EUDOnStart(_warning)
