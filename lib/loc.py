from eudplib import *


def _locfgen(mod1, mod2, mod3, mod4):

    @EUDFunc
    def _locf(epd, x, y):
        act = Forward()

        VProc(epd, [
            epd.AddNumber(EPD(0x58DC60)),
            epd.QueueAssignTo(EPD(act) + 4)
        ])
        VProc(x, x.QueueAssignTo(EPD(act) + 5))

        VProc(epd, [
            epd.AddNumber(1),
            SetMemory(epd._varact + 16, Add, 8)
        ])
        VProc(y, y.QueueAssignTo(EPD(act) + 5 + 8))

        VProc(epd, [
            epd.AddNumber(1),
            SetMemory(epd._varact + 16, Add, 8)
        ])
        VProc(x, SetMemory(x._varact + 16, Add, 16))

        VProc(epd, [
            epd.AddNumber(1),
            SetMemory(epd._varact + 16, Add, 8)
        ])
        VProc(y, SetMemory(y._varact + 16, Add, 16))

        DoActions([
            act << SetMemory(0, mod1, 0),
            SetMemory(0, mod2, 0),
            SetMemory(0, mod3, 0),
            SetMemory(0, mod4, 0),
        ])

    return _locf


_SetLoc = _locfgen(SetTo, SetTo, SetTo, SetTo)
_AddLoc = _locfgen(Add, Add, Add, Add)
_ResizeLoc = _locfgen(Subtract, Subtract, Add, Add)


def SetLoc(locID, x, y):
    _SetLoc(locID * 5, x, y)


def AddLoc(locID, x, y):
    _AddLoc(locID * 5, x, y)


def ResizeLoc(locID, x, y):
    _ResizeLoc(locID * 5, x, y)


@EUDFunc
def _GetLocTL(epd):
    epd += EPD(0x58DC60)
    EUDReturn(
        f_dwread_epd(epd),
        f_dwread_epd(epd + 1))


def GetLocTL(locID):
    # 로케이션의 위(top), 왼쪽 (left) 좌표를 얻어냅니다.
    # @param  {[type]} locID 로케이션 번호. $L(로케이션 이름) 으로 얻을 수 있습니다.
    return _GetLocTL(locID * 5)
