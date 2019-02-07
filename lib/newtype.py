from eudplib import *
from eudplib.eudlib.eudarray import EUDArrayData

try:
    MemoryXEPD
except (NameError):
    from eudx import MemoryXEPD, MemoryX, SetMemoryX


class Uint8ArrayData(EUDArrayData):
    def GetDataSize(self):
        return self._arrlen

    def WritePayload(self, buf):
        for item in self._datas:
            buf.WriteByte(item)

    # --------

    def AtLeast(self, key, value):
        return MemoryEPD(EPD(self) + key, AtLeast, value)

    def AtMost(self, key, value):
        return MemoryEPD(EPD(self) + key, AtMost, value)

    def Exactly(self, key, value):
        return MemoryEPD(EPD(self) + key, Exactly, value)

    def get(self, key):
        if isinstance(key, EUDVariable):
            key, subp = f_div(key, 4)
        else:
            key, subp = divmod(key, 4)
        return f_bread_epd(EPD(self) + key, subp)

    def __getitem__(self, key):
        return self.get(key)

    def set(self, key, item):
        if isinstance(key, EUDVariable):
            key, subp = f_div(key, 4)
        else:
            key, subp = divmod(key, 4)
        return f_bwrite_epd(EPD(self) + key, subp, item)

    def __setitem__(self, key, item):
        return self.set(key, item)


class Uint8Array(ExprProxy):
    def __init__(self, initval=None, *, _from=None):
        if _from is not None:
            dataObj = _from

        else:
            dataObj = Uint8ArrayData(initval)
            self.length = dataObj._arrlen

        super().__init__(dataObj)
        self._epd = EPD(self)
        self.dontFlatten = True

    def AtLeast(self, key, value):
        return MemoryEPD(self._epd + key, AtLeast, value)

    def AtMost(self, key, value):
        return MemoryEPD(self._epd + key, AtMost, value)

    def Exactly(self, key, value):
        return MemoryEPD(self._epd + key, Exactly, value)

    def AtLeastX(self, key, value):
        key, subp = divmod(key, 4)
        return MemoryXEPD(self._epd + key, AtLeast, value, 255 * 256 ** subp)

    def AtMostX(self, key, value):
        key, subp = divmod(key, 4)
        return MemoryXEPD(self._epd + key, AtMost, value, 255 * 256 ** subp)

    def ExactlyX(self, key, value):
        key, subp = divmod(key, 4)
        return MemoryXEPD(self._epd + key, Exactly, value, 255 * 256 ** subp)

    def get(self, key):
        if isinstance(key, int):
            key, subp = divmod(key, 4)
        else:
            key, subp = f_div(key, 4)
        return f_bread_epd(self._epd + key, subp)

    def __getitem__(self, key):
        return self.get(key)

    def set(self, key, item):
        if isinstance(key, EUDVariable):
            key, subp = f_div(key, 4)
        else:
            key, subp = divmod(key, 4)
        return f_bwrite_epd(self._epd + key, subp, item)

    def __setitem__(self, key, item):
        return self.set(key, item)


class PVariable:
    def __init__(self, initvars=None):
        self.variables = EUDVArray(8)(initvars)

    @EUDTypedMethod([TrgPlayer], [None])
    def _getitem(self, player):
        _temp = EUDVariable()
        EUDSwitch(player)
        for p in range(8):
            EUDSwitchCase()(p)
            _temp << self.variables[p]
            EUDBreak()
        EUDEndSwitch()
        return _temp

    def __getitem__(self, player):
        player = EncodePlayer(player)
        try:
            return self.variables[player]
        except (TypeError):
            return self._getitem(player)

    def __len__(self):
        return len(self.variables)

    @EUDTypedMethod([TrgPlayer, None])
    def _setitem(self, player, item):
        EUDSwitch(player)
        for p in range(8):
            EUDSwitchCase()(p)
            self.variables[p].Assign(item)
            EUDBreak()
        EUDEndSwitch()

    def __setitem__(self, player, item):
        player = EncodePlayer(player)
        try:
            self.variables[player].Assign(item)
        except (TypeError):
            self._setitem(player, item)

    def __iter__(self):
        return iter(self.variables)


chkt = GetChkTokenized()
ownr = chkt.getsection("OWNR")
human = [p for p in range(12) if ownr[p] == 6]


def p2i(player):
    if not isinstance(player, int):
        raise EPError
    return human.index(player)


class HVariable(PVariable):
    def __init__(self, initvars=None):
        self.variables = EUDVArray(len(human))(initvars)

    @EUDTypedMethod([TrgPlayer], [None])
    def _getitem(self, player):
        _temp = EUDVariable()
        EUDSwitch(player)
        for p in human:
            EUDSwitchCase()(p)
            _temp << self.variables[p2i(p)]
            EUDBreak()
        EUDEndSwitch()
        EUDReturn(_temp)

    def __getitem__(self, player):
        player = EncodePlayer(player)
        try:
            return self.variables[p2i(player)]
        except (EPError):
            return self._getitem(player)

    @EUDTypedMethod([TrgPlayer, None])
    def _setitem(self, player, item):
        EUDSwitch(player)
        for p in human:
            EUDSwitchCase()(p)
            self.variables[p2i(p)].Assign(item)
            EUDBreak()
        EUDEndSwitch()

    def __setitem__(self, player, item):
        player = EncodePlayer(player)
        try:
            self.variables[p2i(player)].Assign(item)
        except (EPError):
            self._setitem(player, item)
