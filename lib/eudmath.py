import texteffect as te
from eudplib import *


@EUDFunc
def f_abs(x):
    """return |x|"""
    if EUDIf()(x >= 0x80000000):
        x << -x
    EUDEndIf()
    EUDReturn(x)


@EUDFunc
def f_hypot(x, y):
    """hypotenuse approximation: a + (b + max(0, b + b - a)) ÷ 5
    """
    for v in (x, y):
        if EUDIf()(v >= 0x80000000):
            v << -v
        EUDEndIf()

    t = EUDVariable()
    if EUDIfNot()(x >= y):
        # Swap x, y so that x >= y
        """
        t << x
        x << y
        y << t
        """
        nt1 = Forward()
        RawTrigger(
            nextptr=x.GetVTable(),
            actions=[
                x.QueueAssignTo(t),
                y.QueueAssignTo(x),
                t.QueueAssignTo(y),
                SetNextPtr(x.GetVTable(), y.GetVTable()),
                SetNextPtr(y.GetVTable(), t.GetVTable()),
                SetNextPtr(t.GetVTable(), nt1),
            ]
        )
        nt1 << NextTrigger()
    EUDEndIf()
    """
    t = y + y - x
    if EUDIf()(t >= 0x80000000):
        t << 0
    EUDEndIf()
    t += y
    """
    nt2 = Forward()
    RawTrigger(
        nextptr=y.GetVTable(),
        actions=[
            y.QueueAssignTo(t),
            t.QueueAddTo(t),
            x.QueueSubtractTo(t),
            SetNextPtr(y.GetVTable(), t.GetVTable()),
            SetNextPtr(t.GetVTable(), x.GetVTable()),
            SetNextPtr(x.GetVTable(), nt2),
        ]
    )
    nt2 << NextTrigger()
    VProc(y, SetMemory(y._varact + 24, SetTo, 0x082D0000))
    hypot = x + t // 5
    EUDReturn(hypot)


@EUDFunc
def f_pos2xy(a, b):
    dx, dy = EUDCreateVariables(2)
    origcp = f_getcurpl()
    comparer = [Forward() for _ in range(26)]
    DoActions([dx.SetNumber(0), dy.SetNumber(0), SetCurrentPlayer(a)
               ] + [SetMemory(c + 4, SetTo, b) for c in comparer])
    for x in range(13):
        RawTrigger(
            conditions=[
                DeathsX(CurrentPlayer, AtLeast, 1, 2**x),
                comparer[x] << MemoryX(0, AtLeast, 1, 2**x)
            ],
            actions=dx.AddNumber(2**x)
        )
    for y in range(16, 29):
        RawTrigger(
            conditions=[
                DeathsX(CurrentPlayer, AtLeast, 1, 2**y),
                comparer[y - 3] << MemoryX(0, AtLeast, 1, 2**y)
            ],
            actions=dy.AddNumber(2**y)
        )
    f_setcurpl(origcp)
    EUDReturn(dx, dy)
