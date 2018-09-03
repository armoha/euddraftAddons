from eudplib import *


@EUDFunc
def SetLoc(locID, x, y):
    DoActions([
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID, SetTo, x),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 1, SetTo, y),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 2, SetTo, x),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 3, SetTo, y),
    ])


@EUDFunc
def AddLoc(locID, x, y):
    DoActions([
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID, Add, x),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 1, Add, y),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 2, Add, x),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 3, Add, y),
    ])


@EUDFunc
def ResizeLoc(locID, x, y):
    DoActions([
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID, Subtract, x),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 1, Subtract, y),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 2, Add, x),
        SetMemoryEPD(EPD(0x58DC60) + 5 * locID + 3, Add, y),
    ])


@EUDFunc
def f_getLocTL(locID):
    # 로케이션의 위(top), 왼쪽 (left) 좌표를 얻어냅니다.
    # @param  {[type]} locID 로케이션 번호. $L(로케이션 이름) 으로 얻을 수 있습니다.
    EUDReturn(
        f_dwread_epd(EPD(0x58DC60) + 5 * locID + 0),
        f_dwread_epd(EPD(0x58DC60) + 5 * locID + 1))


@EUDFunc
def SetLocEPD(locID, epd):
    xy = f_dwread_epd(epd)
    x, y = f_dwbreak(xy)[0:2]
    SetLoc(locID, x, y)
