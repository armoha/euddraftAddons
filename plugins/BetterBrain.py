from eudplib import *

try:
    from eudx import MemoryX
except (ImportError):
    class ConditionX(Condition):
        def __init__(
            self, locid, player, amount, unitid, comparison, condtype, restype, flags
        ):
            super().__init__(
                locid, player, amount, unitid, comparison, condtype, restype, flags
            )

            self.fields = [
                locid,
                player,
                amount,
                unitid,
                comparison,
                condtype,
                restype,
                flags,
                b2i2(b"SC"),
            ]

    def DeathsX(Player, Comparison, Number, Unit, Mask):
        Player = EncodePlayer(Player, issueError=True)
        Comparison = EncodeComparison(Comparison, issueError=True)
        Unit = EncodeUnit(Unit, issueError=True)
        return ConditionX(Mask, Player, Number, Unit, Comparison, 15, 0, 0)

    def MemoryX(dest, cmptype, value, mask):
        return DeathsX(EPD(dest), cmptype, value, 0, mask)

def afterTriggerExec():
    for i in range(1700):
        ptr = 0x59CCA8 + 336 * i
        RawTrigger(
            conditions=[
                Memory(ptr + 0x38, Exactly, 0),
                Memory(ptr + 0x3C, Exactly, 0),
                Memory(ptr + 0x40, Exactly, 0),
                MemoryX(ptr + 0x20, Exactly, 0x12, 0xFF)
            ],
            actions=SetMemory(ptr + 0x20, Subtract, 0x12)
        )
