# -*- coding: utf-8 -*-
from eudplib import *
from operator import itemgetter
'''
[detectchat]
__addr__ : 0x58D900
chat to be detected : value
__patternAddr__ : address to get matched pattern value
__lenAddr__ : address to get chat length
__ptrAddr__ : address to get chat address
^start.*middle.*end$ : value
'''


def onInit():
    global Addr, lenAddr, ptrAddr, patternAddr
    # defaults
    Addr, lenAddr, ptrAddr, patternAddr = 0x58D900, 0, 0, 0
    chatList, regexList = [], []

    for k, v in settings.items():
        rL = k.split('.*')
        if k[:1] == '^' and k[-1:] == '$' and len(rL) == 3:
            regexList.append([rL[0][1:], rL[1], rL[2][:-1], int(v, 0)])
        elif k == '__addr__':
            try:
                Addr = int(v, 0)
            except (ValueError):
                raise EPError('__addr__ value should be integer; %s' % v)
        elif k == '__lenAddr__':
            try:
                lenAddr = int(v, 0)
            except (ValueError):
                raise EPError('__lenAddr__ value should be integer; %s' % v)
        elif k == '__ptrAddr__':
            try:
                ptrAddr = int(v, 0)
            except (ValueError):
                raise EPError('__ptrAddr__ value should be integer; %s' % v)
        elif k == '__patternAddr__':
            try:
                patternAddr = int(v, 0)
            except (ValueError):
                raise EPError(
                    '__patternAddr__ value should be integer; %s' % v)
        else:
            if v == '1' or v == '0':
                raise EPError('Increment value should be at least 2')
            chatList.append([k.strip(), int(v, 0)])

    chatList.sort(key=itemgetter(1, 0))
    regexList.sort()
    print(
        '\n'.join(chatList),
        "1 : player did chat, but chat doen't match any pattern\n",
        '__addr__ : %s\n' % hex(Addr),
        '__lenAddr__ : %s\n' % hex(lenAddr),
        '__ptrAddr__ : %s\n' % hex(ptrAddr),
        'Condition for detecting player chat:\n',
        '   Memory(%s, Exactly, (LEFT VALUE));\n',
        '\n__patternAddr__ : %s' % hex(patternAddr)
    )
    for r in regexList:
        print('{3} : ^{0}.*{1}.*{2}$'.format(*r))

    chatSet = set()
    global minlen, maxlen
    minlen, maxlen = 78, 0
    for s in chatList:
        t = s[0].encode('UTF-8')
        chatSet.add((t, s[1]))
        if len(t) > 78:
            raise EPError("User can type chat up to 78 bytes in SC.")
        if len(t) > maxlen:
            maxlen = len(t)
        if len(t) < minlen:
            minlen = len(t)
    global chatDict
    chatDict = [0 for _ in range(maxlen - minlen + 1)]
    chatList = list(chatSet)
    for s in chatList:
        size = len(s[0]) - minlen
        if isinstance(chatDict[size], list):
            chatDict[size][0].append(Db(s[0] + b'\0'))
            chatDict[size][1].append(s[1])
        else:
            chatDict[size] = [[Db(s[0] + b'\0')], [s[1]]]
    for i, s in enumerate(chatDict):
        if isinstance(s, list):
            chatDict[i] = EUDArray([len(s[0])] + s[0] + s[1])
    chatDict = EUDArray(chatDict)

    rSet = set()
    for r in regexList:
        e = 'UTF-8'
        rSet.add((r[0].encode(e), r[1].encode(e), r[2].encode(e), r[3]))
    global rList, rListlen
    rList = list(rSet)
    for i, r in enumerate(rList):
        rList[i] = EUDArray([
            Db(r[0] + b'\0'), Db(r[1] + b'\0'), Db(r[2] + b'\0'),
            r[3], len(r[0]), len(r[2])
        ])
    rListlen = len(rList)
    rList = EUDArray(rList)


onInit()

try:
    from strlib import f_memcmp, f_strlen, f_strnstr
except (ImportError):
    from eudplib.eudlib.stringf.rwcommon import br1, br2

    @EUDFunc
    def f_memcmp(str1, str2, count):
        c = EUDVariable()
        c << count
        br1.seekoffset(str1)
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
        EUDReturn(ret)

    @EUDFunc
    def f_strnstr(string, substring, count):
        # O(mn)
        br1.seekoffset(string)
        br2.seekoffset(substring)
        dst = EUDVariable()
        dst << -1

        b = br2.readbyte()
        if EUDIf()(b == 0):
            EUDReturn(string)
        EUDEndIf()
        if EUDWhile()(count >= 1):
            a = br1.readbyte()
            dst += 1
            count -= 1
            if EUDIf()(EUDSCOr()(a == 0)()):
                EUDBreak()
            if EUDElseIfNot()(a == b):
                EUDContinue()
            EUDEndIf()
            br1_epdoffset = br1._offset
            br1_suboffset = br1._suboffset
            if EUDWhile()(1):
                c = br2.readbyte()
                if EUDIf()(c == 0):
                    EUDReturn(string + dst)
                if EUDElseIfNot()(br1.readbyte() == c):
                    EUDBreak()
                EUDEndIf()
            EUDEndWhile()
            br1.seekepd(br1_epdoffset)
            br1._suboffset = br1_suboffset
            br2.seekoffset(substring + 1)
        EUDEndWhile()
        EUDReturn(-1)


try:
    from eudx import EUDXMemoryEPD, EUDXSetMemoryEPD
except (ImportError):
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

    def EUDXSetMemoryEPD(dest, modtype, value, mask):
        dest = EncodePlayer(dest, issueError=True)
        modtype = EncodeModifier(modtype, issueError=True)
        return EUDXAction(mask, 0, 0, 0, dest, value, 0, 45, modtype, 20)


class Con:
    def __init__(self, epd):
        self.epd = epd
        self.locid = epd
        self.player = epd + 1
        self.amount = epd + 2
        self.unitid = epd + 3  # w
        self.comparison = epd + 3  # b
        self.condtype = epd + 3  # b
        self.restype = epd + 4  # b
        self.flags = epd + 4  # b
        self.internal = epd + 4  # w


class Act:
    def __init__(self, epd):
        self.epd = epd
        self.locid1 = epd
        self.strid = epd + 1
        self.wavid = epd + 2
        self.time = epd + 3
        self.player1 = epd + 4
        self.player2 = epd + 5  # dest locid, CUWP #, number, AI script, switch
        self.unitid = epd + 6  # w
        self.acttype = epd + 6  # b
        self.amount = epd + 6  # b
        self.flags = epd + 7  # b
        self.internal = epd + 7  # b3


class CTrig:
    def __init__(self, epd):
        self.epd = epd
        self.prev = epd
        self.next = epd + 1
        self.con = [Con(epd + 2 + 5 * n) for n in range(16)]
        self.act = [Act(epd + 82 + 8 * n) for n in range(64)]


@EUDFunc
def Init():
    player_number = f_dwread_epd(EPD(0x57F1B0))
    name_ptr = 0x57EEEB + 36 * player_number
    name_len = f_strlen(name_ptr)

    global ChatEvent
    ChatEvent = [Forward() for _ in range(12)]
    _ChatEvent = EUDArray([EPD(t) for t in ChatEvent])
    for index in EUDLoopRange(11):
        offset = 218 * index + name_len
        q, r = f_div(offset, 4)
        chat = EPD(0x640B60) + q
        t = CTrig(_ChatEvent[index])

        DoActions([
            SetMemoryEPD(t.con[0].player, SetTo, chat),
            SetMemoryEPD(t.con[1].player, SetTo, chat + 1),
            SetMemoryEPD(t.act[0].player1, SetTo, chat),
            SetMemoryEPD(t.act[1].player1, SetTo, chat + 1),
            SetMemoryEPD(t.act[2].player2, SetTo, 0x640B60 + offset + 3),
        ])

        EUDSwitch(r)

        # CASE 0 - NAME<:7 C>HAT
        if EUDSwitchCase()(0):
            DoActions([  # swap <07> and whitespace to prevent re-detection
                SetMemoryEPD(t.con[0].locid, SetTo, 0xFFFFFF),
                SetMemoryEPD(t.con[0].amount, SetTo, b2i4(b':\x07 \x00')),
                SetMemoryEPD(t.con[1].amount, SetTo, 0),
                EUDXSetMemoryEPD(t.con[1].comparison, SetTo, 0, 0xFF0000),
                SetMemoryEPD(t.act[0].locid1, SetTo, 0xFFFFFF),
                SetMemoryEPD(t.act[0].player2, SetTo, b2i4(b': \x07\x00')),
                EUDXSetMemoryEPD(t.act[0].amount, SetTo, 0x7000000, 0xFF000000),
                SetMemoryEPD(t.act[1].player2, SetTo, 0),
                EUDXSetMemoryEPD(t.act[1].amount, SetTo, 0x8000000, 0xFF000000)
            ])
            EUDBreak()

        # CASE 1 - NAME<1:7 >CHAT
        if EUDSwitchCase()(1):
            DoActions([
                SetMemoryEPD(t.con[0].locid, SetTo, 0xFFFFFF00),
                SetMemoryEPD(t.con[0].amount, SetTo, b2i4(b'\x00:\x07 ')),
                SetMemoryEPD(t.con[1].amount, SetTo, 0),
                EUDXSetMemoryEPD(t.con[1].comparison, SetTo, 0, 0xFF0000),
                SetMemoryEPD(t.act[0].locid1, SetTo, 0xFFFFFF00),
                SetMemoryEPD(t.act[0].player2, SetTo, b2i4(b'\x00: \x07')),
                EUDXSetMemoryEPD(t.act[0].amount, SetTo, 0x7000000, 0xFF000000),
                SetMemoryEPD(t.act[1].player2, SetTo, 0),
                EUDXSetMemoryEPD(t.act[1].amount, SetTo, 0x8000000, 0xFF000000)
            ])
            EUDBreak()

        # CASE 2 - NAME<12:7>< CHA>T
        if EUDSwitchCase()(2):
            DoActions([
                SetMemoryEPD(t.con[0].locid, SetTo, 0xFFFF0000),
                SetMemoryEPD(t.con[0].amount, SetTo, b2i4(b'\x00\x00:\x07')),
                SetMemoryEPD(t.con[1].locid, SetTo, 0xFF),
                SetMemoryEPD(t.con[1].amount, SetTo, b2i1(b' ')),
                EUDXSetMemoryEPD(t.con[1].comparison, SetTo, 10, 0xFF0000),
                SetMemoryEPD(t.act[0].locid1, SetTo, 0xFFFF0000),
                SetMemoryEPD(t.act[0].player2, SetTo, b2i4(b'\x00\x00: ')),
                EUDXSetMemoryEPD(t.act[0].amount, SetTo, 0x7000000, 0xFF000000),
                SetMemoryEPD(t.act[1].locid1, SetTo, 0xFF),
                SetMemoryEPD(t.act[1].player2, SetTo, b2i1(b'\x07')),
                EUDXSetMemoryEPD(t.act[1].amount, SetTo, 0x7000000, 0xFF000000)
            ])
            EUDBreak()

        # CASE 3 - NAME<123:><7 CH>AT
        if EUDSwitchCase()(3):
            DoActions([
                SetMemoryEPD(t.con[0].locid, SetTo, 0xFF000000),
                SetMemoryEPD(t.con[0].amount, SetTo, b2i4(b'\x00\x00\x00:')),
                SetMemoryEPD(t.con[1].locid, SetTo, 0xFFFF),
                SetMemoryEPD(t.con[1].amount, SetTo, b2i2(b'\x07 ')),
                EUDXSetMemoryEPD(t.con[1].comparison, SetTo, 10, 0xFF0000),
                SetMemoryEPD(t.act[0].player2, SetTo, 0),
                EUDXSetMemoryEPD(t.act[0].amount, SetTo, 0x8000000, 0xFF000000),
                SetMemoryEPD(t.act[1].locid1, SetTo, 0xFFFF),
                SetMemoryEPD(t.act[1].player2, SetTo, b2i2(b' \x07')),
                EUDXSetMemoryEPD(t.act[1].amount, SetTo, 0x7000000, 0xFF000000)
            ])
            EUDBreak()

        EUDEndSwitch()


def onPluginStart():
    Init()


def beforeTriggerExec():
    if EUDIf()(Memory(Addr, Exactly, -1)):
        Init()
    EUDEndIf()

    chat_ptr = EUDVariable()
    DoActions([
        SetMemory(Addr, SetTo, 0),
        SetMemory(patternAddr, SetTo, 0) if rListlen >= 1 else [],
        chat_ptr.SetNumber(0),
        [SetNextPtr(ChatEvent[i], ChatEvent[i + 1]) for i in range(11)]
    ])

    ChatDetected = Forward()
    for i in range(11):
        ChatEvent[i] << RawTrigger(
            conditions=[
                EUDXMemoryEPD(0, Exactly, 0, 0xFFFFFFFF),
                EUDXMemoryEPD(0, AtLeast, 0, 0xFFFFFFFF)
            ],
            actions=[
                EUDXSetMemoryEPD(0, Add, 0, 0xFFFFFFFF),
                EUDXSetMemoryEPD(0, Add, 0, 0xFFFFFFFF),
                chat_ptr.SetNumber(0),
                SetNextPtr(ChatEvent[i], ChatDetected)
            ]
        )

    ChatDetected << NextTrigger()
    chat_len = f_strlen(chat_ptr)
    DoActions([
        SetMemory(Addr, SetTo, 1),
        SetMemory(lenAddr, SetTo, chat_len) if lenAddr >= 1 else [],
        SetMemory(ptrAddr, SetTo, chat_ptr) if ptrAddr >= 1 else []
    ])
    if EUDIf()([
        chat_len >= minlen,
        chat_len <= maxlen
    ]):
        t = EUDArray.cast(chatDict[chat_len - minlen])
        if EUDIf()(t >= 1):
            n = t[0]
            i = EUDVariable()
            i << 1
            if EUDWhile()(i <= n):
                if EUDIf()(f_strcmp(chat_ptr, t[i]) == 0):
                    DoActions(SetMemory(Addr, SetTo, t[n + i]))
                    EUDJump(ChatEvent[-1])
                EUDEndIf()
                i += 1
            EUDEndWhile()
        EUDEndIf()
    EUDEndIf()
    if rListlen >= 1:
        for i in EUDLoopRange(rListlen):
            subArray = EUDArray.cast(rList[i])
            endlen = subArray[5]
            if EUDIf()(
                EUDSCAnd()
                (f_memcmp(chat_ptr, subArray[0], subArray[4]) == 0)
                (f_memcmp(chat_ptr + chat_len -
                          endlen, subArray[2], endlen) == 0)
                (f_strnstr(chat_ptr, subArray[1], chat_len) != -1)
                    ()):
                DoActions(SetMemory(patternAddr, SetTo, subArray[3]))
                EUDJump(ChatEvent[-1])
            EUDEndIf()

    ChatEvent[11] << NextTrigger()
