from eudplib import *


@EUDFunc
def f_dwepdCUnitread_epd(targetplayer):
    origcp = f_getcurpl()
    ptr, epd = EUDVariable(), EUDVariable()
    fin, restore = [Forward() for i in range(2)]
    DoActions([
        ptr.SetNumber(0x59CCA8),
        epd.SetNumber(EPD(0x59CCA8)),
        SetMemory(0x6509B0, SetTo, targetplayer),
        SetMemory(restore + 20, SetTo, 0),
    ])

    for i in range(10, -1, -1):
        RawTrigger(
            conditions=[
                Deaths(CurrentPlayer, AtLeast, 0x59CCA8 + 336 * 2**i, 0)
            ],
            actions=[
                SetDeaths(CurrentPlayer, Subtract, 336 * 2**i, 0),
                ptr.AddNumber(336 * 2 ** i),
                epd.AddNumber(84 * 2 ** i),
                SetMemory(restore + 20, Add, 336 * 2**i)
            ]
        )
    EUDJumpIf(Deaths(CurrentPlayer, Exactly, 0x59CCA8, 0), fin)
    RawTrigger(
        actions=[
            ptr.SetNumber(0),
            epd.SetNumber(0),
        ]
    )
    fin << RawTrigger(actions=[
        restore << SetDeaths(CurrentPlayer, Add, 0xEDAC, 0)
    ])
    f_setcurpl(origcp)

    EUDReturn(ptr, epd)


def LoopNewUnit():
    firstUnitPtr = 0x628430
    EUDCreateBlock('newunitloop', firstUnitPtr)
    ptr, epd = f_dwepdCUnitread_epd(EPD(firstUnitPtr))
    tos0 = EUDLightVariable()
    tos0 << 0

    if EUDWhile()(ptr >= 1):
        targetOrderSpecial = f_dwread_epd(epd + 0xA5 // 4) & 0xFF00
        if EUDIf()(targetOrderSpecial >= 0x100):
            f_dwsubtract_epd(epd + 0xA5 // 4, targetOrderSpecial)
            yield ptr, epd
        if EUDElse()():
            DoActions(tos0.AddNumber(1))
            EUDBreakIf(tos0.AtLeast(2))
        EUDEndIf()
        EUDSetContinuePoint()
        SetVariables([ptr, epd], f_dwepdCUnitread_epd(epd + 1))
    EUDEndWhile()

    EUDPopBlock('newunitloop')


cpoffset = EUDVariable()
initcp = Forward()


@EUDFunc
def f_setcp(targetplayer):
    DoActions([
        initcp << SetMemory(0x6509B0, Subtract, 0xEDAC),
        SetMemory(0x6509B0, Add, targetplayer),
        SetMemory(initcp + 20, SetTo, targetplayer),
        cpoffset.SetNumber(targetplayer)
    ])


def f_cp(offset):
    f_setcp(offset // 4)


def CPLoopUnit():
    initialEPD = EPD(0x59CCA8) + 0x0C // 4
    oldcp = f_getcurpl()
    DoActions([
        SetMemory(0x6509B0, SetTo, initialEPD),
        SetMemory(initcp + 20, SetTo, 0x0C // 4),
        cpoffset.SetNumber(0x0C // 4),
    ])
    if EUDLoopN()(1700):
        if EUDIf()(Deaths(CurrentPlayer, AtLeast, 1, 0)):
            yield cpoffset
            f_cp(0x0C)
        EUDEndIf()
        DoActions(SetMemory(0x6509B0, Add, 336 // 4))
    EUDEndLoopN()

    f_setcurpl(oldcp)


def LoopPUnit(player_number):
    firstPlayerUnitPtr = 0x6283F8 + 4 * player_number
    EUDCreateBlock('playerunitloop', firstPlayerUnitPtr)
    ptr, epd = f_dwepdCUnitread_epd(EPD(firstPlayerUnitPtr))

    if EUDWhile()(ptr >= 1):
        yield ptr, epd
        EUDSetContinuePoint()
        # /*0x06C*/ BW::CUnit*  nextPlayerUnit;
        SetVariables([ptr, epd], f_dwepdCUnitread_epd(epd + 0x6C // 4))
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
