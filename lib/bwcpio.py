from eudplib.eudlib.memiof import (
    dwepdio as dwm,
    cpmemio as cpm,
    byterw as brw,
    modcurpl as cp,
)
from eudplib import (
    core as c,
    ctrlstru as cs,
    utils as ut,
)


@c.EUDFunc
def f_bwrite_cp(cpo, subp, b):
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions([
        c.SetMemory(0x6509B0, c.Add, cpo),
        c.SetMemory(cpaddact_number, c.SetTo, 0),
    ])
    cs.EUDSwitch(subp)
    for i in range(4):
        cs.EUDSwitchCase()(i)
        for j in range(31, -1, -1):
            if 8 * (i + 1) <= j:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2**j),
                    ]
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                    ]
                )

            if j == 8 * i:
                break

        cs.DoActions(c.SetDeaths(c.CurrentPlayer, c.Add, b * (256 ** i), 0))
        cs.EUDBreak()
    cs.EUDEndSwitch()
    cs.DoActions([
        cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0),
        c.SetMemory(0x6509B0, c.Add, -cpo),
    ])


@c.EUDFunc
def f_wwrite_cp(cpo, subp, w):
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions([
        c.SetMemory(0x6509B0, c.Add, cpo),
        c.SetMemory(cpaddact_number, c.SetTo, 0),
    ])
    cs.EUDSwitch(subp)
    for i in range(3):
        cs.EUDSwitchCase()(i)
        for j in range(31, -1, -1):
            if 8 * (i + 2) <= j:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2**j),
                    ]
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                    ]
                )

            if j == 8 * i:
                break

        cs.DoActions(c.SetDeaths(c.CurrentPlayer, c.Add, w * (256 ** i), 0))
        cs.EUDBreak()

    if cs.EUDSwitchCase()(3):
        b0, b1 = dwm.f_dwbreak(w)[2:4]
        f_bwrite_cp(0, 3, b0)
        f_bwrite_cp(1, 0, b1)

    cs.EUDEndSwitch()
    cs.DoActions([
        cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0),
        c.SetMemory(0x6509B0, c.Add, -cpo)
    ])


@c.EUDFunc
def f_bread_cp(cpo, subp):
    b = c.EUDVariable()
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions([
        c.SetMemory(0x6509B0, c.Add, cpo),
        b.SetNumber(0),
        c.SetMemory(cpaddact_number, c.SetTo, 0),
    ])
    cs.EUDSwitch(subp)
    for i in range(4):
        cs.EUDSwitchCase()(i)
        for j in range(31, -1, -1):
            if 8 * i <= j < 8 * (i + 1):
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2**j),
                        b.AddNumber(2**(j - 8 * i))
                    ]
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2**j),
                    ]
                )

            if j == 8 * i:
                break

        cs.EUDBreak()
    cs.EUDEndSwitch()
    cs.DoActions([cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])
    cs.DoActions(c.SetMemory(0x6509B0, c.Add, -cpo))
    return b


@c.EUDFunc
def f_wread_cp(cpo, subp):
    w = c.EUDVariable()
    cpaddact = c.Forward()
    cpaddact_number = cpaddact + 20
    cs.DoActions([
        c.SetMemory(0x6509B0, c.Add, cpo),
        w.SetNumber(0),
        c.SetMemory(cpaddact_number, c.SetTo, 0),
    ])
    cs.EUDSwitch(subp)
    for i in range(3):
        cs.EUDSwitchCase()(i)
        for j in range(31, -1, -1):
            if 8 * i <= j < 8 * (i + 2):
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2**j),
                        w.AddNumber(2**(j - 8 * i))
                    ]
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(cpaddact_number, c.Add, 2**j),
                    ]
                )

            if j == 8 * i:
                break

        cs.EUDBreak()

    if cs.EUDSwitchCase()(3):
        w << f_bread_cp(0, 3) + f_bread_cp(1, 0) * 256

    cs.EUDEndSwitch()
    cs.DoActions([
        cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0),
        c.SetMemory(0x6509B0, c.Add, -cpo)
    ])
    return w
