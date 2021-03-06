from eudplib import *


v = EUDVArray(11)()


def Timeline(loopn, interval=1):
    """시간에 따라서 어떤 일이 진행되게 하는 함수입니다.

    for t in Timeline(60):
        내용물

    이라고 하면 매 트리거루프마다 t가 0, 1, 2, 3, ... , 58, 59, 0, 1, ... 으로
    바뀌면서 내용물이 실행되게 됩니다. 미사일 패턴을 짤 때 잘 애용하고 있습니다.

    foreach에 들어가는 함수는 아직 eps로 짤 수 없어서 .py로 함수를 만들었습니다.
    """
    v = EUDVariable()
    i, t = [EUDLightVariable() for _ in range(2)]
    t << 0
    if EUDWhile()(t == 0):
        vt = EUDVariable()  # Temporary variable
        vt << v
        yield vt
        EUDSetContinuePoint()
        i += 1
        t << 1
    EUDEndWhile()
    if EUDIf()(i >= interval):
        v += 1
        i << 0
    EUDEndIf()
    Trigger(v == loopn, v.SetNumber(0))


def Timeless(loopn, interval=1, index=0):
    i, t = [EUDLightVariable() for _ in range(2)]
    t << 0
    if EUDWhile()(t == 0):
        vt = EUDVariable()  # Temporary variable
        vt << v[index]
        yield vt
        EUDSetContinuePoint()
        i += 1
        t << 1
    EUDEndWhile()
    if EUDIf()(i >= interval):
        v[index] += 1
        i << 0
    EUDEndIf()
    if EUDIf()(v[index] == loopn):
        v[index] -= 1
    EUDEndIf()
