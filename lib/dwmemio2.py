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
def f_wread2_epd(epd, subp):
    oldcp = cp.f_getcurpl()
    w = c.EUDVariable()
    addact = c.Forward()
    addact_number = addact + 20
    cs.DoActions([
        c.SetCurrentPlayer(epd),
        w.SetNumber(0),
        c.SetMemory(addact_number, c.SetTo, 0),
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
                        c.SetMemory(addact_number, c.Add, 2**j),
                        w.AddNumber(2**j)
                    ]
                )
            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(addact_number, c.Add, 2**j),
                    ]
                )
            if j == 8 * i:
                break
        cs.EUDBreak()
    # Things gets complicated on this case.
    # We won't hand-optimize this case. This is a very, very rare case
    if cs.EUDSwitchCase()(3):
        w << f_bread2_cp(0, 3) + f_bread2_cp(1, 0)
    cs.EUDEndSwitch()
    cs.DoActions([
        addact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0),
        c.SetCurrentPlayer(oldcp),
    ])
    return w
    

@c.EUDFunc
def f_bread2_epd(epd, subp):
    oldcp = cp.f_getcurpl()
    b = c.EUDVariable()
    addact = c.Forward()
    addact_number = addact + 20
    cs.DoActions([
        c.SetCurrentPlayer(epd),
        b.SetNumber(0),
        c.SetMemory(addact_number, c.SetTo, 0),
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
                        c.SetMemory(addact_number, c.Add, 2**j),
                        b.AddNumber(2**j)
                    ]
                )
            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        c.SetMemory(addact_number, c.Add, 2**j),
                    ]
                )
            if j == 8 * i:
                break
        cs.EUDBreak()
    cs.EUDEndSwitch()
    cs.DoActions([
        addact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0),
        c.SetCurrentPlayer(oldcp),
    ])
    return b


@c.EUDFunc
def f_bread2_cp(cpo, subp):
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
                        b.AddNumber(2**j)
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
def f_wread2_cp(cpo, subp):
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
        w << f_bread2_cp(0, 3) + f_bread2_cp(1, 0)
    cs.EUDEndSwitch()
    cs.DoActions([
        cpaddact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0),
        c.SetMemory(0x6509B0, c.Add, -cpo)
    ])
    return w
