from eudplib import *

n = 29244 // 4 - 1
noAir = Forward()
isFinish = Forward()


def onPluginStart():
    reph_epd = f_epdread_epd(EPD(0x6D5CD8))
    DoActions([
        SetMemory(noAir + 16, SetTo, reph_epd),  # Act + 16: group/player
        SetMemory(isFinish + 8, SetTo, reph_epd + n),  # Con + 8: amount
    ])


def beforeTriggerExec():
    trg = [Forward() for i in range(3)]

    trg[0] << RawTrigger(
        actions=[
            noAir << SetDeaths(0xBABE, SetTo, 0, 0),
            SetMemory(noAir + 16, Add, 1)
        ]
    )

    trg[1] << RawTrigger(
        nextptr=trg[0],
        conditions=[
            isFinish << Memory(noAir + 16, Exactly, 0xEDAC)
        ],
        actions=SetNextPtr(trg[1], trg[2])
    )

    trg[2] << RawTrigger(
        actions=[
            SetMemory(noAir + 16, Subtract, n),
            SetNextPtr(trg[1], trg[0])
        ]
    )
