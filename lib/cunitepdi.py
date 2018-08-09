from eudplib import (
    core as c,
    ctrlstru as cs,
    utils as ut,
)

from eudplib.eudlib.memiof.modcurpl import (
    f_setcurpl,
    f_getcurpl,
)


@c.EUDFunc
def f_dwepdcunitread_epd(targetplayer):
    origcp = f_getcurpl()
    ptr, epd = c.EUDVariable(), c.EUDVariable()
    addact = c.Forward()
    addact_number = addact + 20
    cs.DoActions([
        ptr.SetNumber(0x59CCA8),
        epd.SetNumber(ut.EPD(0x59CCA8)),
        c.SetMemory(0x6509B0, c.SetTo, targetplayer),
        c.SetMemory(addact_number, c.SetTo, 0),
    ])
    for i in range(10, -1, -1):
        c.RawTrigger(
            conditions=[
                c.Deaths(c.CurrentPlayer, c.AtLeast, 0x59CCA8 + 336 * 2**i, 0)
            ],
            actions=[
                c.SetDeaths(c.CurrentPlayer, c.Subtract, 336 * 2**i, 0),
                ptr.AddNumber(336 * 2 ** i),
                epd.AddNumber(84 * 2 ** i),
                c.SetMemory(addact_number, c.Add, 336 * 2**i),
            ]
        )

    fin = c.Forward()
    cs.EUDJumpIf(c.Deaths(c.CurrentPlayer, c.Exactly, 0x59CCA8, 0), fin)
    c.RawTrigger(actions=[ptr.SetNumber(0),
                          epd.SetNumber(0)])
    fin << c.RawTrigger(actions=[addact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])
    f_setcurpl(origcp)

    return ptr, epd


@c.EUDFunc
def f_dwcunitread_epd(targetplayer):
    origcp = f_getcurpl()
    ptr = c.EUDVariable()
    addact = c.Forward()
    addact_number = addact + 20
    cs.DoActions([
        ptr.SetNumber(0x59CCA8),
        c.SetMemory(0x6509B0, c.SetTo, targetplayer),
        c.SetMemory(addact_number, c.SetTo, 0),
    ])
    for i in range(10, -1, -1):
        c.RawTrigger(
            conditions=[
                c.Deaths(c.CurrentPlayer, c.AtLeast, 0x59CCA8 + 336 * 2**i, 0)
            ],
            actions=[
                c.SetDeaths(c.CurrentPlayer, c.Subtract, 336 * 2**i, 0),
                ptr.AddNumber(336 * 2 ** i),
                c.SetMemory(addact_number, c.Add, 336 * 2**i),
            ]
        )

    fin = c.Forward()
    cs.EUDJumpIf(c.Deaths(c.CurrentPlayer, c.Exactly, 0x59CCA8, 0), fin)
    c.RawTrigger(actions=ptr.SetNumber(0))
    fin << c.RawTrigger(actions=[addact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])
    f_setcurpl(origcp)

    return ptr


def f_epdcunitread_epd(targetplayer):
    return f_dwepdcunitread_epd(targetplayer)[1]
