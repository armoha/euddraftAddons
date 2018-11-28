from eudplib import core as c
from eudplib import ctrlstru as cs
from eudplib import utils as ut


@c.EUDFunc
def f_dwepdcunitread_epd_safe(targetplayer):
    ret, retepd = c.EUDVariable(), c.EUDVariable()

    # Common comparison rawtrigger
    c.PushTriggerScope()
    cmpc = c.Forward()
    cmp_player = cmpc + 4
    cmp_number = cmpc + 8
    cmpact = c.Forward()

    cmptrigger = c.Forward()
    cmptrigger << c.RawTrigger(
        conditions=[cmpc << c.Memory(0, c.AtMost, 0)],
        actions=[cmpact << c.SetMemory(cmptrigger + 4, c.SetTo, 0)],
    )
    cmpact_ontrueaddr = cmpact + 20
    c.PopTriggerScope()

    # static_for
    chain1 = [c.Forward() for _ in range(11)]
    chain2 = [c.Forward() for _ in range(11)]

    # Main logic start
    error = 1
    c.SeqCompute(
        [
            (ut.EPD(cmp_player), c.SetTo, targetplayer),
            (ut.EPD(cmp_number), c.SetTo, 0x59CCA8 + 336 * (0x7FF - error)),
            (ret, c.SetTo, 0x59CCA8 + 336 * (0x7FF - error)),
            (retepd, c.SetTo, ut.EPD(0x59CCA8) + 84 * (0x7FF - error)),
        ]
    )

    readend = c.Forward()

    for i in range(10, -1, -1):
        nextchain = chain1[i - 1] if i > 0 else readend
        epdsubact = [retepd.AddNumber(-84 * 2 ** i)]
        epdaddact = [retepd.AddNumber(84 * 2 ** i)]

        chain1[i] << c.RawTrigger(
            nextptr=cmptrigger,
            actions=[
                c.SetMemory(cmp_number, c.Subtract, 336 * 2 ** i),
                c.SetNextPtr(cmptrigger, chain2[i]),
                c.SetMemory(cmpact_ontrueaddr, c.SetTo, nextchain),
                ret.SubtractNumber(336 * 2 ** i),
            ]
            + epdsubact,
        )

        chain2[i] << c.RawTrigger(
            actions=[
                c.SetMemory(cmp_number, c.Add, 336 * 2 ** i),
                ret.AddNumber(336 * 2 ** i),
            ]
            + epdaddact
        )

    readend << c.NextTrigger()

    c.RawTrigger(
        conditions=ret.AtMost(0x59CCA7), actions=[ret.SetNumber(0), retepd.SetNumber(0)]
    )
    c.RawTrigger(
        conditions=ret.AtLeast(0x628299),
        actions=[ret.SetNumber(0), retepd.SetNumber(0)],
    )

    return ret, retepd


def f_dwcunitread_epd_safe(targetplayer):
    return f_dwepdcunitread_epd_safe(targetplayer)[0]


def f_epdcunitread_epd_safe(targetplayer):
    return f_dwepdcunitread_epd_safe(targetplayer)[1]
