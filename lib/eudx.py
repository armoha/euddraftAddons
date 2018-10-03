from eudplib import *
'SC:R EUD eXtended thanks to 0xeb, trgk'


class EUDXCondition(Condition):

    def __init__(self, locid, player, amount, unitid,
                 comparison, condtype, restype, flags):
        super().__init__(locid, player, amount, unitid,
                         comparison, condtype, restype, flags)

        self.fields = [locid, player, amount, unitid,
                       comparison, condtype, restype, flags,
                       b2i2(b'SC')]


def EUDXDeaths(Player, Comparison, Number, Unit, Mask):
    Player = EncodePlayer(Player, issueError=True)
    Comparison = EncodeComparison(Comparison, issueError=True)
    Unit = EncodeUnit(Unit, issueError=True)
    return EUDXCondition(Mask, Player, Number, Unit, Comparison, 15, 0, 0)


def EUDXMemory(dest, cmptype, value, mask):
    return EUDXDeaths(EPD(dest), cmptype, value, 0, mask)


def EUDXMemoryEPD(dest, cmptype, value, mask):
    return EUDXDeaths(dest, cmptype, value, 0, mask)


class EUDXAction(Action):

    def __init__(self, locid1, strid, wavid, time, player1, player2,
                 unitid, acttype, amount, flags):
        super().__init__(locid1, strid, wavid, time, player1, player2,
                         unitid, acttype, amount, flags)

        self.fields = [locid1, strid, wavid, time, player1,
                       player2, unitid, acttype, amount, flags,
                       0, b2i2(b'SC')]


def EUDXSetDeaths(Player, Modifier, Number, Unit, Mask):
    Player = EncodePlayer(Player, issueError=True)
    Modifier = EncodeModifier(Modifier, issueError=True)
    Unit = EncodeUnit(Unit, issueError=True)
    return EUDXAction(Mask, 0, 0, 0, Player, Number, Unit, 45, Modifier, 20)


def EUDXSetMemory(dest, modtype, value, mask):
    modtype = EncodeModifier(modtype, issueError=True)
    return EUDXAction(mask, 0, 0, 0, EPD(dest), value, 0, 45, modtype, 20)


def EUDXSetMemoryEPD(dest, modtype, value, mask):
    dest = EncodePlayer(dest, issueError=True)
    modtype = EncodeModifier(modtype, issueError=True)
    return EUDXAction(mask, 0, 0, 0, dest, value, 0, 45, modtype, 20)


def f_maskread_epd(targetplayer, mask, _readerdict={}):

    if mask in _readerdict:
        readerf = _readerdict[mask]
    else:
        def binary_decomposition(x):
            p = 2 ** (int(x).bit_length() - 1)
            while p:
                if p & x:
                    yield p
                p //= 2

        @EUDFunc
        def readerf(targetplayer):
            origcp = f_getcurpl()
            f_setcurpl(targetplayer)

            resetteract = Forward()
            ret = EUDVariable()

            # All set to 0
            RawTrigger(
                actions=[
                    SetMemory(resetteract + 20, SetTo, 0),
                    ret.SetNumber(0)
                ]
            )

            # Fill flags
            for i in binary_decomposition(mask):
                RawTrigger(
                    conditions=[
                        EUDXDeaths(CurrentPlayer, AtLeast, i, 0, mask)
                    ],
                    actions=[
                        EUDXSetDeaths(CurrentPlayer, Subtract, i, 0, mask),
                        SetMemory(resetteract + 20, Add, i),
                        ret.AddNumber(i)
                    ]
                )

            RawTrigger(actions=[
                resetteract << EUDXSetDeaths(CurrentPlayer, Add, 0, 0, mask)
            ])
            f_setcurpl(origcp)

            return ret

        _readerdict[mask] = readerf

    return readerf(targetplayer)
