from eudplib import core as c
from eudplib import ctrlstru as cs
from eudplib import utils as ut


@c.EUDFunc
def _cunitreader():
    ptr, epd = c.EUDVariable(), c.EUDVariable()
    addact = c.Forward()
    addact_number = addact + 20
    cs.DoActions(
        [
            ptr.SetNumber(0x59CCA8),
            epd.SetNumber(ut.EPD(0x59CCA8)),
            c.SetMemory(addact_number, c.SetTo, 0),
        ]
    )
    for i in range(10, -1, -1):
        c.RawTrigger(
            conditions=[
                c.Deaths(c.CurrentPlayer, c.AtLeast, 0x59CCA8 + 336 * 2 ** i, 0)
            ],
            actions=[
                c.SetDeaths(c.CurrentPlayer, c.Subtract, 336 * 2 ** i, 0),
                ptr.AddNumber(336 * 2 ** i),
                epd.AddNumber(84 * 2 ** i),
                c.SetMemory(addact_number, c.Add, 336 * 2 ** i),
            ],
        )
    c.RawTrigger(actions=[addact << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)])

    return ptr, epd


def f_dwepdcunitread_cp(cpo):
    if not isinstance(cpo, int) or cpo != 0:
        cs.DoActions(c.SetMemory(0x6509B0, c.Add, cpo))
    ptr, epd = _cunitreader()
    if not isinstance(cpo, int) or cpo != 0:
        cs.DoActions(c.SetMemory(0x6509B0, c.Add, -cpo))
    return ptr, epd


def f_dwcunitread_cp(cpo):
    return f_dwepdcunitread_cp(cpo)[0]


def f_epdcunitread_cp(cpo):
    return f_dwepdcunitread_cp(cpo)[1]
