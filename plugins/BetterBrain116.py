from eudplib import *


def afterTriggerExec():
    origcp = f_getcurpl()
    epd = EPD(0x59CCA8) + 84 * 0

    c = [Forward() for _ in range(3)]
    a = [Forward() for _ in range(1)]
    _cont, _skipif, _start, _cntpt, _end = [Forward() for _ in range(5)]

    RawTrigger(  # Init
        actions=[
            SetMemory(_skipif + 20, SetTo, _start),
            SetMemory(0x6509B0, SetTo, epd + 0x20 // 4),
            SetMemory(c[0] + 4, SetTo, epd + 0x38 // 4),
            SetMemory(c[1] + 4, SetTo, epd + 0x3C // 4),
            SetMemory(c[2] + 4, SetTo, epd + 0x40 // 4),
            SetMemory(a[0] + 20, SetTo, 0),
            SetNextPtr(_cont, _cntpt)
        ]
    )

    _skipif << RawTrigger(
        conditions=[
            c[0] << MemoryEPD(epd + 0x38 // 4, Exactly, 0),
            c[1] << MemoryEPD(epd + 0x3C // 4, Exactly, 0),
            c[2] << MemoryEPD(epd + 0x40 // 4, Exactly, 0)
        ],
        actions=SetNextPtr(_skipif, _cont)
    )

    _start << NextTrigger()
    for j in range(31, 7, -1):
        RawTrigger(
            conditions=Deaths(CurrentPlayer, AtLeast, 2**j, 0),
            actions=[
                SetDeaths(CurrentPlayer, Subtract, 2**j, 0),
                SetMemory(a[0] + 20, Add, 2**j)
            ]
        )
    RawTrigger(
        conditions=Deaths(CurrentPlayer, Exactly, 0x12, 0),
        actions=SetDeaths(CurrentPlayer, SetTo, 0, 0)
    )
    DoActions([a[0] << SetDeaths(CurrentPlayer, Add, 0, 0)])

    _cont << RawTrigger(
        conditions=Memory(0x6509B0, Exactly, epd + 84 * 1699),
        actions=SetNextPtr(_cont, _end)
    )
    _cntpt << RawTrigger(
        nextptr=_skipif,
        actions=[
            SetMemory(0x6509B0, Add, 84),
            SetMemory(c[0] + 4, Add, 84),
            SetMemory(c[1] + 4, Add, 84),
            SetMemory(c[2] + 4, Add, 84),
            SetMemory(a[0] + 20, SetTo, 0)
        ]
    )

    _end << NextTrigger()
    f_setcurpl(origcp)
