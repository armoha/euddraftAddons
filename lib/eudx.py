from eudplib import *
'SC:R EUD eXtended thanks to 0xeb, trgk'


class ConditionX(Condition):

    def __init__(self, locid, player, amount, unitid,
                 comparison, condtype, restype, flags):
        super().__init__(locid, player, amount, unitid,
                         comparison, condtype, restype, flags)

        self.fields = [locid, player, amount, unitid,
                       comparison, condtype, restype, flags,
                       b2i2(b'SC')]


def DeathsX(Player, Comparison, Number, Unit, Mask):
    Player = EncodePlayer(Player, issueError=True)
    Comparison = EncodeComparison(Comparison, issueError=True)
    Unit = EncodeUnit(Unit, issueError=True)
    return ConditionX(Mask, Player, Number, Unit, Comparison, 15, 0, 0)


def MemoryX(dest, cmptype, value, mask):
    return DeathsX(EPD(dest), cmptype, value, 0, mask)


def MemoryXEPD(dest, cmptype, value, mask):
    return DeathsX(dest, cmptype, value, 0, mask)


class ActionX(Action):

    def __init__(self, locid1, strid, wavid, time, player1, player2,
                 unitid, acttype, amount, flags):
        super().__init__(locid1, strid, wavid, time, player1, player2,
                         unitid, acttype, amount, flags)

        self.fields = [locid1, strid, wavid, time, player1,
                       player2, unitid, acttype, amount, flags,
                       0, b2i2(b'SC')]


def SetDeathsX(Player, Modifier, Number, Unit, Mask):
    Player = EncodePlayer(Player, issueError=True)
    Modifier = EncodeModifier(Modifier, issueError=True)
    Unit = EncodeUnit(Unit, issueError=True)
    return ActionX(Mask, 0, 0, 0, Player, Number, Unit, 45, Modifier, 20)


def SetMemoryX(dest, modtype, value, mask):
    modtype = EncodeModifier(modtype, issueError=True)
    return ActionX(mask, 0, 0, 0, EPD(dest), value, 0, 45, modtype, 20)


def SetMemoryXEPD(dest, modtype, value, mask):
    dest = EncodePlayer(dest, issueError=True)
    modtype = EncodeModifier(modtype, issueError=True)
    return ActionX(mask, 0, 0, 0, dest, value, 0, 45, modtype, 20)


def f_maskread_epd(targetplayer, mask, _readerdict={}):

    if mask in _readerdict:
        readerf = _readerdict[mask]
    else:
        def bits(n):
            while n:
                b = n & (~n+1)
                yield b
                n ^= b

        @EUDFunc
        def readerf(targetplayer):
            origcp = f_getcurpl()
            f_setcurpl(targetplayer)

            ret = EUDVariable()
            ret << 0

            # Fill flags
            for i in bits(mask):
                RawTrigger(
                    conditions=[
                        DeathsX(CurrentPlayer, Exactly, i, 0, i)
                    ],
                    actions=[
                        ret.AddNumber(i)
                    ]
                )

            f_setcurpl(origcp)

            return ret

        _readerdict[mask] = readerf

    return readerf(targetplayer)
