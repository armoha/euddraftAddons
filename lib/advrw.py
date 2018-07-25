# advanced read/write
from eudplib.eudlib.memiof import (
    dwepdio as dwm,
    cpmemio as cpm,
    # byterw as brw,
    # modcurpl as cp,
)
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


@c.EUDFunc
def f_dwepdCUnitread_epd(targetplayer):
    origcp = f_getcurpl()
    ptr, epd = c.EUDVariable(), c.EUDVariable()
    fin, restore = [c.Forward() for i in range(2)]
    cs.DoActions([
        ptr.SetNumber(0x59CCA8),
        epd.SetNumber(ut.EPD(0x59CCA8)),
        c.SetMemory(0x6509B0, c.SetTo, targetplayer),
        c.SetMemory(restore + 20, c.SetTo, 0),
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
                c.SetMemory(restore + 20, c.Add, 336 * 2**i),
            ]
        )

    cs.EUDJumpIf(c.Deaths(c.CurrentPlayer, c.Exactly, 0x59CCA8, 0), fin)
    cs.DoActions([
        ptr.SetNumber(0),
        epd.SetNumber(0),
    ])
    fin << c.RawTrigger(actions=[
        restore << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)
    ])
    f_setcurpl(origcp)

    c.EUDReturn(ptr, epd)


@c.EUDFunc
def f_dwCUnitread_epd(targetplayer):
    origcp = f_getcurpl()
    ptr = c.EUDVariable()
    fin, restore = [c.Forward() for i in range(2)]
    cs.DoActions([
        ptr.SetNumber(0x59CCA8),
        c.SetMemory(0x6509B0, c.SetTo, targetplayer),
        c.SetMemory(restore + 20, c.SetTo, 0),
    ])
    for i in range(10, -1, -1):
        c.RawTrigger(
            conditions=[
                c.Deaths(c.CurrentPlayer, c.AtLeast, 0x59CCA8 + 336 * 2**i, 0)
            ],
            actions=[
                c.SetDeaths(c.CurrentPlayer, c.Subtract, 336 * 2**i, 0),
                ptr.AddNumber(336 * 2 ** i),
                c.SetMemory(restore + 20, c.Add, 336 * 2**i),
            ]
        )

    cs.EUDJumpIf(c.Deaths(c.CurrentPlayer, c.Exactly, 0x59CCA8, 0), fin)
    cs.DoActions(ptr.SetNumber(0))
    fin << c.RawTrigger(actions=[
        restore << c.SetDeaths(c.CurrentPlayer, c.Add, 0xEDAC, 0)
    ])
    f_setcurpl(origcp)

    c.EUDReturn(ptr)


def f_epdCUnitread_epd(targetplayer):
    return f_dwepdCUnitread_epd(targetplayer)[1]


@c.EUDFunc
def f_dwepdCUnitread_epd_safe(targetplayer):
    ret, retepd = c.EUDVariable(), c.EUDVariable()

    # Common comparison rawtrigger
    c.PushTriggerScope()
    cmpc = c.Forward()
    cmp_player = cmpc + 4
    cmp_number = cmpc + 8
    cmpact = c.Forward()

    cmptrigger = c.Forward()
    cmptrigger << c.RawTrigger(
        conditions=[
            cmpc << c.Memory(0, c.AtMost, 0)
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
        (ut.EPD(cmp_player), c.SetTo, targetplayer),
        (ut.EPD(cmp_number), c.SetTo, 0x59CCA8 + 0x7FF * 336),
        (ret, c.SetTo, 0x59CCA8 + 0x7FF * 336),
        (retepd, c.SetTo, ut.EPD(0x59CCA8) + 0x7FF * 84)
    ])

    readend = c.Forward()

    for i in range(10, -1, -1):
        nextchain = chain1[i - 1] if i > 0 else readend
        epdsubact = [retepd.AddNumber(-84 * 2**i)]
        epdaddact = [retepd.AddNumber(84 * 2**i)]

        chain1[i] << c.RawTrigger(
            nextptr=cmptrigger,
            actions=[
                c.SetMemory(cmp_number, c.Subtract, 336 * 2**i),
                c.SetNextPtr(cmptrigger, chain2[i]),
                c.SetMemory(cmpact_ontrueaddr, c.SetTo, nextchain),
                ret.SubtractNumber(336 * 2**i),
            ] + epdsubact
        )

        chain2[i] << c.RawTrigger(
            actions=[
                c.SetMemory(cmp_number, c.Add, 336 * 2**i),
                ret.AddNumber(336 * 2**i),
            ] + epdaddact
        )

    readend << c.NextTrigger()

    return ret, retepd


def f_dwCUnitread_epd_safe(targetplayer):
    return f_dwepdCUnitread_epd_safe(targetplayer)[0]


def f_epdCUnitread_epd_safe(targetplayer):
    return f_dwepdCUnitread_epd_safe(targetplayer)[1]


@c.EUDFunc
def f_bwrite_cp(cpo, subp, b):
    k = c.EUDVariable()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, cpo)],
        k.SetNumber(0),
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
                        k.AddNumber(2**j),
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

        c.SeqCompute([
            (c.EncodePlayer(c.CurrentPlayer), c.Add, k),
            (c.CurrentPlayer, c.Add, b * (256 ** i))
        ])
        cs.EUDBreak()
    cs.EUDEndSwitch()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, -cpo)],
    ])
    return b


@c.EUDFunc
def f_wwrite_cp(cpo, subp, w):
    k = c.EUDVariable()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, cpo)],
        k.SetNumber(0),
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
                        k.AddNumber(2**j),
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

        c.SeqCompute([
            (c.CurrentPlayer, c.Add, k),
            (c.CurrentPlayer, c.Add, w * (256 ** i)),
        ])
        cs.EUDBreak()

    if cs.EUDSwitchCase()(3):
        b0, b1 = dwm.f_dwbreak(w)[2:4]
        f_bwrite_cp(0, 3, b0)
        f_bwrite_cp(1, 0, b1)

    cs.EUDEndSwitch()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, -cpo)],
    ])


@c.EUDFunc
def f_wread_cp(cpo, subp):
    w = c.EUDVariable()
    k = c.EUDVariable()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, cpo)],
        w.SetNumber(0),
        k.SetNumber(0),
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
                        k.AddNumber(2**j),
                        w.AddNumber(2**(j - 8 * i))
                    ]
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        k.AddNumber(2**j),
                    ]
                )

            if j == 8 * i:
                break

        c.SeqCompute([(c.EncodePlayer(c.CurrentPlayer), c.Add, k)])
        cs.EUDBreak()

    if cs.EUDSwitchCase()(3):
        dw0 = cpm.f_dwread_cp(0)
        dw1 = cpm.f_dwread_cp(1)
        w << dwm.f_dwbreak(dw0)[5] + dwm.f_dwbreak(dw1)[2] * 256

    cs.EUDEndSwitch()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, -cpo)],
    ])
    return w


@c.EUDFunc
def f_bread_cp(cpo, subp):
    b = c.EUDVariable()
    k = c.EUDVariable()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, cpo)],
        b.SetNumber(0),
        k.SetNumber(0),
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
                        k.AddNumber(2**j),
                        b.AddNumber(2**(j - 8 * i))
                    ]
                )

            else:
                c.RawTrigger(
                    conditions=c.Deaths(c.CurrentPlayer, c.AtLeast, 2**j, 0),
                    actions=[
                        c.SetDeaths(c.CurrentPlayer, c.Subtract, 2**j, 0),
                        k.AddNumber(2**j),
                    ]
                )

            if j == 8 * i:
                break

        c.SeqCompute([(c.EncodePlayer(c.CurrentPlayer), c.Add, k)])
        cs.EUDBreak()
    cs.EUDEndSwitch()
    cs.DoActions([
        [[] if cpo is 0 else c.SetMemory(0x6509B0, c.Add, -cpo)],
    ])
    return b
