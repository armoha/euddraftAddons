from eudplib import *
'SC:R EUD eXtended thanks to 0xeb, trgk'
tmp = EUDLightVariable()
_tmp = tmp.getValueAddr()


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


def BitOREPD(epd, b):
    return SetMemoryXEPD(epd, SetTo, ~0, b)


def BitANDEPD(epd, b):
    return SetMemoryXEPD(epd, SetTo, 0, ~b)


def BitXOREPD(epd, b):
    c = Forward()
    ret = [
        SetMemory(c + 20, SetTo, a),
        SetMemoryXEPD(epd, SetTo, ~0, b),
        SetMemoryX(c + 20, SetTo, 0, ~b),
        c << SetMemoryEPD(epd, Subtract, 0xEDAC)
    ]
    return ret


def f_omeread_epd(targetplayer, mask, *args, _readerdict={}):
    funcs = [a[0] for a in args]
    initvals = [a[1] for a in args]

    def bits(n):
        n = n & 0xFFFFFFFF
        while n:
            b = n & (~n+1)
            if not all(f(b) == 0 for f in funcs):
                yield b
            n ^= b

    key = (
        tuple(b for b in bits(mask)),
        tuple(initvals),
        tuple(tuple(f(b) for b in bits(mask)) for f in funcs)
    )

    if key in _readerdict:
        readerf = _readerdict[key]
    else:
        @EUDFunc
        def readerf(targetplayer):
            origcp = f_getcurpl()
            f_setcurpl(targetplayer)

            ret = [EUDVariable() for _ in args]
            DoActions([
                ret[i].SetNumber(v)
                for i, v in enumerate(initvals)
            ])

            # Fill flags
            for i in bits(mask):
                RawTrigger(
                    conditions=[
                        DeathsX(CurrentPlayer, Exactly, i, 0, i)
                    ],
                    actions=[
                        [] if f(i) == 0
                        else ret[k].AddNumber(f(i))
                        for k, f in enumerate(funcs)
                    ]
                )

            f_setcurpl(origcp)

            return List2Assignable(ret)

        _readerdict[key] = readerf

    return readerf(targetplayer)


def f_dwepdread_epd(targetplayer, mask=~0):
    return f_omeread_epd(
        targetplayer, mask,
        (lambda a: a, 0),
        (lambda b: b // 4, EPD(0))
    )


def f_dwread_epd(targetplayer, mask=~0):
    return f_omeread_epd(
        targetplayer, mask,
        (lambda a: a, 0)
    )


def f_epdread_epd(targetplayer, mask=~0):
    return f_omeread_epd(
        targetplayer, mask,
        (lambda b: b // 4, EPD(0))
    )


def f_wwread_epd(targetplayer, subp):
    i = 256 ** subp
    return f_omeread_epd(
        targetplayer, 65535 * i,
        (lambda a: a // i, 0)
    )


def f_bread_epd(targetplayer, subp):
    i = 256 ** subp
    return f_omeread_epd(
        targetplayer, 256 * i - 1,
        (lambda a: a // i, 0)
    )


def _omeread_cp(mask, *args, _readerdict={}):
    funcs = [a[0] for a in args]
    initvals = [a[1] for a in args]

    def bits(n):
        n = n & 0xFFFFFFFF
        while n:
            b = n & (~n+1)
            if not all(f(b) == 0 for f in funcs):
                yield b
            n ^= b

    key = (
        tuple(b for b in bits(mask)),
        tuple(initvals),
        tuple(tuple(f(b) for b in bits(mask)) for f in funcs)
    )

    if key in _readerdict:
        readerf = _readerdict[key]
    else:
        @EUDFunc
        def readerf():

            ret = [EUDVariable() for _ in args]
            DoActions([
                ret[i].SetNumber(v)
                for i, v in enumerate(initvals)
            ])

            # Fill flags
            for i in bits(mask):
                RawTrigger(
                    conditions=[
                        DeathsX(CurrentPlayer, Exactly, i, 0, i)
                    ],
                    actions=[
                        [] if f(i) == 0
                        else ret[k].AddNumber(f(i))
                        for k, f in enumerate(funcs)
                    ]
                )

            return List2Assignable(ret)

        _readerdict[key] = readerf

    return readerf()


def f_omeread_cp(cpoffset, mask, *args):
    if cpoffset != 0:
        DoActions(SetMemory(0x6509B0, Add, cpoffset))
    ret = _omeread_cp(mask, *args)
    if cpoffset != 0:
        DoActions(SetMemory(0x6509B0, Add, -cpoffset))
    return List2Assignable(ret)


def f_dwepdread_cp(cpoffset, mask=~0):
    return f_omeread_cp(
        cpoffset, mask,
        (lambda a: a, 0),
        (lambda b: b // 4, EPD(0))
    )


def f_dwread_cp(cpoffset, mask=~0):
    return f_omeread_cp(
        cpoffset, mask,
        (lambda a: a, 0)
    )


def f_epdread_cp(cpoffset, mask=~0):
    return f_omeread_cp(
        cpoffset, mask,
        (lambda b: b // 4, EPD(0))
    )


def f_wread_cp(cpoffset, subp):
    i = 256 ** subp
    return f_omeread_cp(
        cpoffset, 65535 * i,
        (lambda a: a // i, 0)
    )


def f_bread_cp(cpoffset, subp):
    i = 256 ** subp
    return f_omeread_cp(
        cpoffset, 256 * i - 1,
        (lambda a: a // i, 0)
    )
    

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