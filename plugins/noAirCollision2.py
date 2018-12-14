from eudplib import *

t = [Forward() for _ in range(115)]
j = EUDVariable()


def onPluginStart():
    global reph_epd
    reph_epd = f_epdread_epd(EPD(0x6D5CD8))

    s = EUDArray([EPD(x) for x in t])
    i = EUDVariable()
    if EUDWhile()(i <= 114):
        k = EUDVariable()
        if EUDWhile()(k <= 63 * 8):
            EUDBreakIf([i == 114, k >= 15 * 8])
            DoActions(
                [
                    SetMemoryEPD(s[i] + 86 + k, SetTo, reph_epd + j),
                    k.AddNumber(8),
                    j.AddNumber(1),
                ]
            )
        EUDEndWhile()
        DoActions([i.AddNumber(1), k.SetNumber(0)])
    EUDEndWhile()


def beforeTriggerExec():
    dummy = j.getValueAddr()
    for i in range(114):
        t[i] << RawTrigger(actions=[SetMemory(dummy, SetTo, 0) for _ in range(64)])
    t[114] << RawTrigger(actions=[SetMemory(dummy, SetTo, 0) for _ in range(15)])
