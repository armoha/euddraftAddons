from eudplib import *
try:
    import tempcustomText as ct
except ImportError:
    try:
        import customText4 as ct
    except ImportError:
        try:
            import customText3 as ct
        except ImportError:
            raise EPError("customText 라이브러리가 필요합니다.")
        else:
            print("pname: customText3 사용")
    else:
        print("pname: customText4 사용")
else:
    print("pname: tempcustomText 사용")
from eudplib.eudlib.stringf.rwcommon import br1, br2

baselen = EUDArray(8)


@EUDFunc
def f_memcmp(str1, str2, count):
    c = EUDVariable()
    c << count
    br1.seekepd(str1)
    br2.seekoffset(str2)

    if EUDWhile()(c.AtLeast(1)):
        c -= 1
        ch1 = br1.readbyte()
        ch2 = br2.readbyte()
        if EUDIf()(ch1 == ch2):
            EUDContinue()
        EUDEndIf()
        EUDReturn(ch1 - ch2)
    EUDEndWhile()

    EUDReturn(0)


@EUDFunc
def f_strlen(src):
    ret = EUDVariable()
    ret << 0
    br1.seekoffset(src)
    if EUDWhile()(br1.readbyte() >= 1):
        ret += 1
    EUDEndWhile()
    return ret


odd, even_atLeast, even_atMost, even_exactly = [[Forward() for _ in range(8)] for i in range(4)]
temp = Db(218)
oddA, even_leastA, even_mostA, even_exactlyA = [EUDArray([EPD(x) for x in li]) for li in [odd, even_atLeast, even_atMost, even_exactly]]
L, Lepd = EUDVariable(), EUDVariable()


@EUDFunc
def check_id(player, line, dst):
    ret = EUDVariable()
    ret << 1
    mod = line % 2
    global Lepd
    if EUDIf()(mod == 0):
        Lepd += 1
    EUDEndIf()
    EUDSwitch(player)
    for i in range(8):
        if EUDSwitchCase()(i):
            if EUDIf()(EUDSCAnd()(mod == 0
            )([odd[i] << MemoryEPD(dst + 1, Exactly, 0)])()):
                ret << 0
            if EUDElseIf()(EUDSCAnd()(mod == 1
            )([even_atLeast[i] << MemoryEPD(dst, AtLeast, 0)]
            )([even_atMost[i] << MemoryEPD(dst, AtMost, 0)]
            )([even_exactly[i] << MemoryEPD(dst + 1, Exactly, 0)])()):
                ret << 0
            EUDEndIf()
            EUDBreak()
    EUDEndSwitch()
    return ret
    

def _init():
    if EUDPlayerLoop()():
        playerid = 0x57EEEB + 36 * f_getcurpl()
        ct.f_sprintf(temp, ct.f_str(playerid), ":")
        idlen = f_strlen(playerid)
        o = f_dwread_epd(EPD(temp))
        e0, e1 = f_dwbreak(o)[0:2]
        _e0 = e0 * 65536
        e2 = f_wread_epd(EPD(temp) + 1, 0) * 65536
        oepd, eepd = oddA[f_getcurpl()], even_exactlyA[f_getcurpl()]
        
        DoActions([
            SetMemoryEPD(baselen._epd + f_getcurpl(), SetTo, idlen),
            SetMemoryEPD(oepd + 2, SetTo, o),
            SetMemoryEPD(even_leastA[f_getcurpl()] + 2, SetTo, _e0),
            SetMemoryEPD(even_mostA[f_getcurpl()] + 2, SetTo, _e0 + 0xFFFF),
            SetMemoryEPD(eepd + 2, SetTo, e1 + e2),
        ])
        if EUDIf()(idlen <= 4):
            DoActions([
                SetMemoryEPD(eepd + 2, SetTo, 0),
                SetMemoryEPD(eepd + 3, SetTo, 0x0F000000),
            ])
            if EUDIf()(idlen <= 2):
                DoActions([
                    SetMemoryEPD(oepd + 2, SetTo, 0),
                    SetMemoryEPD(oepd + 3, SetTo, 0x0F000000),
                ])
            EUDEndIf()
        EUDEndIf()
                
    EUDEndPlayerLoop()


EUDOnStart(_init)
isTxtPtrUnchanged = EUDLightVariable()


def Optimize():
    prevPtr, addPtr = Forward(), Forward()

    DoActions(isTxtPtrUnchanged.SetNumber(0))
    RawTrigger(
        conditions=[prevPtr << Memory(0x640B58, Exactly, 0xEDAC)],
        actions=isTxtPtrUnchanged.SetNumber(1),
    )
    if EUDIf()(isTxtPtrUnchanged.Exactly(0)):
        DoActions([
            SetMemory(prevPtr + 8, SetTo, 0),
            SetMemory(addPtr + 20, SetTo, 0),
        ])
        for i in range(3, -1, -1):
            RawTrigger(
                conditions=Memory(0x640B58, AtLeast, 2**i),
                actions=[
                    SetMemory(0x640B58, Subtract, 2**i),
                    SetMemory(addPtr + 20, Add, 2**i),
                    SetMemory(prevPtr + 8, Add, 2**i)
                ]
            )
        DoActions([addPtr << SetMemory(0x640B58, Add, 0)])
    EUDEndIf()
        

def SetName(player, *name):
    _end = Forward()
    EUDJumpIf(isTxtPtrUnchanged.Exactly(1), _end)

    if isUnproxyInstance(player, type(P1)):
        if player == CurrentPlayer:
            player = f_getcurpl()
        else:
            player = EncodePlayer(player)
    EUDJumpIf(f_playerexist(player) == 0, _end)
    bname, blen = EPD(0x57EEEC) + 9 * player, baselen[player]

    global L, Lepd
    L << 0x640B60 - 218
    Lepd << EPD(0x640B60) - 55
    for line in EUDLoopRange(11):
        L += 218
        Lepd += 54
        EUDContinueIf(check_id(player, line, Lepd))
        EUDContinueIf(f_memcmp(bname, L + 1, blen - 1) >= 1)
        f_dbstr_addstr(temp, L + blen)
        ct.f_sprintf(L, *(name + (ct.f_str(temp),)))
    _end << NextTrigger()
