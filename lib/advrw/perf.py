from eudplib import core as c
from eudplib import ctrlstru as cs
from eudplib import utils as ut
from eudplib.eudlib.memiof import byterw as brw
from eudplib.eudlib.memiof import cpmemio as cpm
from eudplib.eudlib.memiof import dwepdio as dwm
from eudplib.eudlib.memiof import modcurpl as cp

from advrw.bwcpio import f_bread_cp


@c.EUDFunc
def f_dwepdread_epd(targetplayer):
    origcp = cp.f_getcurpl()
    ptr, epd = c.EUDVariable(), c.EUDVariable()
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions(
        [
            ptr.SetNumber(0),
            epd.SetNumber(ut.EPD(0)),
            c.SetCurrentPlayer(targetplayer),
            c.SetMemory(cpaddact_number, c.SetTo, 0),
        ]
    )

    for i in range(31, -1, -1):
        c.RawTrigger(
            conditions=[c.Deaths(c.CurrentPlayer, c.AtLeast, 2 ** i, 0)],
            actions=[
                c.SetDeaths(c.CurrentPlayer, c.Subtract, 2 ** i, 0),
                ptr.AddNumber(2 ** i),
                c.SetMemory(cpaddact_number, c.Add, 2 ** i),
                epd.AddNumber(2 ** (i - 2)) if i >= 2 else [],
            ],
        )

    c.RawTrigger(actions=[cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])
    cp.f_setcurpl(origcp)

    return ptr, epd


@c.EUDFunc
def f_dwread_epd(targetplayer):
    origcp = cp.f_getcurpl()
    ptr = c.EUDVariable()
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions(
        [
            ptr.SetNumber(0),
            c.SetCurrentPlayer(targetplayer),
            c.SetMemory(cpaddact_number, c.SetTo, 0),
        ]
    )
    for i in range(31, -1, -1):
        c.RawTrigger(
            conditions=[c.Deaths(c.CurrentPlayer, c.AtLeast, 2 ** i, 0)],
            actions=[
                c.SetDeaths(c.CurrentPlayer, c.Subtract, 2 ** i, 0),
                ptr.AddNumber(2 ** i),
                c.SetMemory(cpaddact_number, c.Add, 2 ** i),
            ],
        )

    c.RawTrigger(actions=[cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])
    cp.f_setcurpl(origcp)

    return ptr


def f_epdread_epd(targetplayer):
    return f_dwepdread_epd(targetplayer)[1]


@c.EUDFunc
def f_wread_epd(epd, subp):
    oldcp = cp.f_getcurpl()
    w = c.EUDVariable()
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions(
        [
            c.SetMemory(0x6509B0, c.SetTo, epd),
            w.SetNumber(0),
            c.SetMemory(cpaddact_number, c.SetTo, 0),
        ]
    )
    cs.EUDSwitch(subp)
    for i in range(3):
        cs.EUDSwitchCase()(i)
        for j in range(31, -1, -1):
            if 8 * i <= j < 8 * (i + 2):
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2 ** j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2 ** j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2 ** j),
                        w.AddNumber(2 ** (j - 8 * i)),
                    ],
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2 ** j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2 ** j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2 ** j),
                    ],
                )

            if j == 8 * i:
                break

        cs.EUDBreak()

    # Things gets complicated on this case.
    # We won't hand-optimize this case. This is a very, very rare case
    if cs.EUDSwitchCase()(3):
        w << f_bread_cp(0, 3) + f_bread_cp(1, 0) * 256

    cs.EUDEndSwitch()
    c.RawTrigger(actions=[cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])
    cp.f_setcurpl(oldcp)
    return w


@c.EUDFunc
def f_bread_epd(epd, subp):
    oldcp = cp.f_getcurpl()
    b = c.EUDVariable()
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions(
        [
            c.SetCurrentPlayer(epd),
            b.SetNumber(0),
            c.SetMemory(cpaddact_number, c.SetTo, 0),
        ]
    )
    cs.EUDSwitch(subp)
    for i in range(4):
        cs.EUDSwitchCase()(i)
        for j in range(31, -1, -1):
            if 8 * i <= j < 8 * (i + 1):
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2 ** j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2 ** j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2 ** j),
                        b.AddNumber(2 ** (j - 8 * i)),
                    ],
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2 ** j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2 ** j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2 ** j),
                    ],
                )

            if j == 8 * i:
                break

        cs.EUDBreak()
    cs.EUDEndSwitch()
    c.RawTrigger(actions=[cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])
    cp.f_setcurpl(oldcp)
    return b
