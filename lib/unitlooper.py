from eudplib import *


@EUDFunc
def f_dwepdcunitread_epd_safe(targetplayer):
    # from advanced read/write functions
    # https://github.com/armoha/euddraftAddons/raw/master/lib/advrw.zip

    ret, retepd = EUDVariable(), EUDVariable()

    # Common comparison rawtrigger
    PushTriggerScope()
    cmpc = Forward()
    cmp_player = cmpc + 4
    cmp_number = cmpc + 8
    cmpact = Forward()

    cmptrigger = Forward()
    cmptrigger << RawTrigger(
        conditions=[
            cmpc << Memory(0, AtMost, 0)
        ],
        actions=[
            cmpact << SetMemory(cmptrigger + 4, SetTo, 0)
        ]
    )
    cmpact_ontrueaddr = cmpact + 20
    PopTriggerScope()

    # static_for
    chain1 = [Forward() for _ in range(11)]
    chain2 = [Forward() for _ in range(11)]

    # Main logic start
    error = 1
    SeqCompute([
        (EPD(cmp_player), SetTo, targetplayer),
        (EPD(cmp_number), SetTo, 0x59CCA8 + 336 * (0x7FF - error)),
        (ret, SetTo, 0x59CCA8 + 336 * (0x7FF - error)),
        (retepd, SetTo, EPD(0x59CCA8) + 84 * (0x7FF - error))
    ])

    readend = Forward()

    for i in range(10, -1, -1):
        nextchain = chain1[i - 1] if i > 0 else readend
        epdsubact = [retepd.AddNumber(-84 * 2 ** i)]
        epdaddact = [retepd.AddNumber(84 * 2 ** i)]

        chain1[i] << RawTrigger(
            nextptr=cmptrigger,
            actions=[
                SetMemory(cmp_number, Subtract, 336 * 2 ** i),
                SetNextPtr(cmptrigger, chain2[i]),
                SetMemory(cmpact_ontrueaddr, SetTo, nextchain),
                ret.SubtractNumber(336 * 2 ** i),
            ] + epdsubact
        )

        chain2[i] << RawTrigger(
            actions=[
                SetMemory(cmp_number, Add, 336 * 2 ** i),
                ret.AddNumber(336 * 2 ** i),
            ] + epdaddact
        )

    readend << NextTrigger()

    RawTrigger(
        conditions=ret.AtMost(0x59CCA7),
        actions=[
            ret.SetNumber(0),
            retepd.SetNumber(0),
        ]
    )
    RawTrigger(
        conditions=ret.AtLeast(0x628299),
        actions=[
            ret.SetNumber(0),
            retepd.SetNumber(0),
        ]
    )

    return ret, retepd


@EUDFunc
def f_bread2_epd(epd, subp):
    oldcp = f_getcurpl()
    b = EUDVariable()
    addact = Forward()
    addact_number = addact + 20
    DoActions([
        SetCurrentPlayer(epd),
        b.SetNumber(0),
        SetMemory(addact_number, SetTo, 0),
    ])
    EUDSwitch(subp)
    for i in range(4):
        EUDSwitchCase()(i)
        for j in range(31, -1, -1):
            if 8 * i <= j < 8 * (i + 1):
                RawTrigger(
                    conditions=Deaths(CurrentPlayer, AtLeast, 2**j, 0),
                    actions=[
                        SetDeaths(CurrentPlayer, Subtract, 2**j, 0),
                        SetMemory(addact_number, Add, 2**j),
                        b.AddNumber(2**j)
                    ]
                )
            else:
                RawTrigger(
                    conditions=Deaths(CurrentPlayer, AtLeast, 2**j, 0),
                    actions=[
                        SetDeaths(CurrentPlayer, Subtract, 2**j, 0),
                        SetMemory(addact_number, Add, 2**j),
                    ]
                )
            if j == 8 * i:
                break
        EUDBreak()
    EUDEndSwitch()
    DoActions([
        addact << SetDeaths(CurrentPlayer, Add, 0xEDAC, 0),
        SetCurrentPlayer(oldcp),
    ])
    return b


def LoopNewUnit():
    firstUnitPtr = EPD(0x628430)
    EUDCreateBlock('newunitloop', 'newlo')
    tos0 = EUDLightVariable()
    tos0 << 0

    ptr, epd = f_dwepdcunitread_epd_safe(firstUnitPtr)
    if EUDWhile()(ptr >= 1):
        targetOrderSpecial = f_bread2_epd(epd + 0xA5 // 4, 1)
        if EUDIf()(targetOrderSpecial >= 0x100):
            f_dwsubtract_epd(epd + 0xA5 // 4, targetOrderSpecial)
            yield ptr, epd
        if EUDElse()():
            DoActions(tos0.AddNumber(1))
            EUDBreakIf(tos0.AtLeast(2))
        EUDEndIf()
        EUDSetContinuePoint()
        SetVariables([ptr, epd], f_dwepdcunitread_epd_safe(epd + 1))
    EUDEndWhile()

    EUDPopBlock('newunitloop')


cpStack, prevcp = [], 0x0C
initcp = Forward()


@EUDFunc
def f_setcp(targetplayer):
    DoActions([
        initcp << SetMemory(0x6509B0, Subtract, 0xEDAC),
        SetMemory(0x6509B0, Add, targetplayer),
        SetMemory(initcp + 20, SetTo, targetplayer),
    ])


def f_cp(offset):
    global prevcp
    if prevcp != offset:
        f_setcp(offset // 4)
        prevcp = offset


def f_cpScope(offset):
    a, b = cpStack[-1], offset
    cpStack.append(b)
    f_cpMove(a, b)
    yield b // 4
    f_cpMove(b, a)
    cpStack.pop()


def _addorsub(d):
    if d >= 0:
        return Add
    else:
        return Subtract


def f_cpMove(a, b):
    d = abs(b // 4 - a // 4)
    DoActions(SetMemory(0x6509B0, _addorsub(b - a), d))
    # print("0x{:X} to 0x{:X}: {._name}, {}.".format(a, b, _addorsub(b - a), d))


def CPLoopUnit():
    initialEPD = EPD(0x59CCA8) + 0x0C // 4
    oldcp = f_getcurpl()
    DoActions([SetMemory(0x6509B0, SetTo, initialEPD),
               SetMemory(initcp + 20, SetTo, 0x0C // 4)])
    global cpStack, prevcp
    cpStack, prevcp = [0x0C], 0x0C
    if EUDLoopN()(1700):
        EUDContinueIf(Deaths(CurrentPlayer, Exactly, 0, 0))
        yield cpStack
        f_cp(0x0C)
        EUDSetContinuePoint()
        DoActions(SetMemory(0x6509B0, Add, 336 // 4))
    EUDEndLoopN()

    f_setcurpl(oldcp)


def LoopPUnit(player_number):
    if player_number == CurrentPlayer or player_number == EncodePlayer(CurrentPlayer):
        player_number = f_getcurpl()
    if isUnproxyInstance(player_number, type(P1)):
        player_number = EncodePlayer(player_number)
    firstPlayerUnitPtr = 0x6283F8 + 4 * player_number
    EUDCreateBlock('playerunitloop', firstPlayerUnitPtr)
    ptr, epd = f_dwepdcunitread_epd_safe(EPD(firstPlayerUnitPtr))

    if EUDWhile()(ptr >= 1):
        yield ptr, epd
        EUDSetContinuePoint()
        # /*0x06C*/ BW::CUnit*  nextPlayerUnit;
        SetVariables([ptr, epd], f_dwepdcunitread_epd_safe(epd + 0x6C // 4))
    EUDEndWhile()

    EUDPopBlock('playerunitloop')


def EUDLoopUnit2():
    # 출처 bwpack by trgk
    # https://github.com/phu54321/bwpack/blob/master/src/unitloopHelper.py
    """EUDLoopUnit보다 약간? 빠릅니다. 유닛 리스트를 따라가지 않고
    1700개 유닛을 도는 방식으로 작동합니다.
    """
    ptr, epd = EUDCreateVariables(2)
    ptr << 0x59CCA8
    epd << EPD(0x59CCA8)
    if EUDLoopN()(1700):
        ptr2, epd2 = EUDCreateVariables(2)
        SetVariables([ptr2, epd2], [ptr, epd])
        # sprite가 NULL이면 없는 유닛으로 판단.
        EUDContinueIf(MemoryEPD(epd + (0x0C // 4), Exactly, 0))
        yield ptr, epd
        EUDSetContinuePoint()
        ptr += 336
        epd += 336 // 4
    EUDEndLoopN()


def _init():
    if EUDIf()(Never()):
        f_setcp(0x0C)
    EUDEndIf()


EUDOnStart(_init)
