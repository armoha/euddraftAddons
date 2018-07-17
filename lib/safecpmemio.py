from eudplib import core as c
from eudplib import ctrlstru as cs
from eudplib import utils as ut


@c.EUDFunc
def _reader():
    ret, retepd = c.EUDVariable(), c.EUDVariable()

    # Common comparison rawtrigger
    c.PushTriggerScope()
    cmpc = c.Forward()
    cmp_number = cmpc + 8
    cmpact = c.Forward()

    cmptrigger = c.Forward()
    cmptrigger << c.RawTrigger(
        conditions=[
            cmpc << c.Deaths(c.CurrentPlayer, c.AtMost, 0, 0)
        ],
        actions=[
            cmpact << c.SetMemory(cmptrigger + 4, c.SetTo, 0)
        ]
    )
    cmpact_ontrueaddr = cmpact + 20
    c.PopTriggerScope()

    # static_for
    chain1 = [c.Forward() for _ in range(32)]
    chain2 = [c.Forward() for _ in range(32)]

    # Main logic start
    c.SeqCompute([
        (ut.EPD(cmp_number), c.SetTo, 0xFFFFFFFF),
        (ret, c.SetTo, 0xFFFFFFFF),
        (retepd, c.SetTo, ut.EPD(0) + 0x3FFFFFFF)
    ])

    readend = c.Forward()

    for i in range(31, -1, -1):
        nextchain = chain1[i - 1] if i > 0 else readend
        if i >= 2:
            epdsubact = [retepd.AddNumber(-2 ** (i - 2))]
            epdaddact = [retepd.AddNumber(2 ** (i - 2))]
        else:
            epdsubact = []
            epdaddact = []

        chain1[i] << c.RawTrigger(
            nextptr=cmptrigger,
            actions=[
                c.SetMemory(cmp_number, c.Subtract, 2 ** i),
                c.SetNextPtr(cmptrigger, chain2[i]),
                c.SetMemory(cmpact_ontrueaddr, c.SetTo, nextchain),
                ret.SubtractNumber(2 ** i),
            ] + epdsubact
        )

        chain2[i] << c.RawTrigger(
            actions=[
                c.SetMemory(cmp_number, c.Add, 2 ** i),
                ret.AddNumber(2 ** i),
            ] + epdaddact
        )

    readend << c.NextTrigger()

    return ret, retepd


def f_dwepdread_cp_safe(cpo):
    if cpo != 0:
        cs.DoActions(c.SetMemory(0x6509B0, c.Add, cpo))
    ptr, epd = _reader()
    if cpo != 0:
        cs.DoActions(c.SetMemory(0x6509B0, c.Add, -cpo))
    return ptr, epd


def f_dwread_cp_safe(cpo):
    return f_dwepdread_cp_safe(cpo)[0]


def f_epdread_cp_safe(cpo):
    return f_dwepdread_cp_safe(cpo)[1]
