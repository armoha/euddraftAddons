from eudplib import *
from eudplib.eudlib.stringf.rwcommon import br1, br2
from operator import itemgetter
'''[채팅인식4]
__addr__ : 0x58D900
__encoding__ : UTF-8, cp949
인식할 말 1 : 값 1
인식할 말 2 : 값 2
^시작.*중간.*끝$ : 값 2
인식할 말 3 : 값 3
...'''


# from my strlib.py https://github.com/armoha/euddraftAddons/blob/master/lib/strlib.py
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


def onInit():
    global Addr, lenAddr, ptrAddr, patternAddr
    Addr = 0x58D900
    lenAddr, ptrAddr, patternAddr = 0, 0, 0
    chatList, regexList = [], []
    chatEncoding = set(['UTF-8'])

    for k, v in settings.items():
        rL = k.split('.*')
        if k[:1] == '^' and k[-1:] == '$' and len(rL) == 3:
            regexList.append([rL[0][1:], rL[1], rL[2][:-1], int(v, 0)])
        elif k == '__addr__':
            try:
                Addr = int(v, 0)  # 주소를 정수로 가져온다.
            except (ValueError):
                raise EPError('오류: __addr__의 값"%s"이 정수가 아닙니다.' % v)
        elif k == '__lenAddr__':
            try:
                lenAddr = int(v, 0)  # 주소를 정수로 가져온다.
            except (ValueError):
                raise EPError('오류: __lenAddr__의 값"%s"이 정수가 아닙니다.' % v)
        elif k == '__ptrAddr__':
            try:
                ptrAddr = int(v, 0)  # 주소를 정수로 가져온다.
            except (ValueError):
                raise EPError('오류: __ptrAddr__의 값"%s"이 정수가 아닙니다.' % v)
        elif k == '__patternAddr__':
            try:
                patternAddr = int(v, 0)  # 주소를 정수로 가져온다.
            except (ValueError):
                raise EPError('오류: __patternAddr__의 값"%s"이 정수가 아닙니다.' % v)
        elif k == '__encoding__':
            chatEncoding = set([_.strip() for _ in v.split(',')])
        else:
            if v == '1' or v == '0':
                raise EPError('오류: 더할 값은 2 이상이어야 합니다.')
            chatList.append([k.strip(), int(v, 0)])

    chatList.sort(key=itemgetter(1, 0))
    regexList.sort()
    for i, s in enumerate(chatList):
        print('{} : {}'.format(s[1], s[0]))
    print('1 : (해당 없음)',
          '__encoding__ : {}'.format(chatEncoding),
          '__addr__ : %s' % hex(Addr),
          '__lenAddr__ : %s' % hex(lenAddr),
          '__ptrAddr__ : %s' % hex(ptrAddr),
          'Memory(%s, Exactly, 왼쪽의 값);을 조건으로 쓰시면 됩니다. 총 개수: %d' % (hex(Addr), len(chatList)), sep='\n')
    for r in regexList:
        print('{3} : ^{0}.*{1}.*{2}$'.format(*r))
    print('__patternAddr__ : %s' % hex(patternAddr))

    chatSet = set()
    global minlen, maxlen
    minlen, maxlen = 78, 0
    for i, s in enumerate(chatList):
        for e in chatEncoding:
            t = s[0].encode(e)
            chatSet.add((t, s[1]))
            if len(t) > 78:
                raise EPError("스타크래프트에서 채팅은 78바이트까지만 입력할 수 있습니다.\n현재 크기: {} > {}".format(len(t), s[0]))
            if len(t) > maxlen:
                maxlen = len(t)
            if len(t) < minlen:
                minlen = len(t)
    global chatDict
    chatDict = [0 for _ in range(maxlen - minlen + 1)]
    chatList = list(chatSet)
    for i, s in enumerate(chatList):
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
        for e in chatEncoding:
            rSet.add((r[0].encode(e), r[1].encode(e), r[2].encode(e), r[3]))
    global rList, rListlen
    rList = list(rSet)
    for i, r in enumerate(rList):
        rList[i] = EUDArray((Db(r[0] + b'\0'), Db(r[1] + b'\0'), Db(r[2] + b'\0'),
                             r[3], len(r[0]), len(r[2])))
    rListlen = len(rList)
    rList = EUDArray(rList)


onInit()

con = [[Forward() for _ in range(2)] for __ in range(5)]
act = [[Forward() for _ in range(2)] for __ in range(5)]
chatptr, exit = EUDVariable(), Forward()
cp = [[Forward() for _ in range(2)] for __ in range(3)]
trg = [Forward() for _ in range(2)]


@EUDFunc
def f_init():
    pNumber = f_dwread_epd(EPD(0x57F1B0))  # 플레이어 번호 (비공유)
    idptr = 0x57EEEB + 36 * pNumber
    idlen = f_strlen(idptr)
    idmod = idlen % 4

    for n in range(2):
        nmod = idmod + (n % 2) * 4
        _end = 0x640B63 + 218 * n + idlen
        trg_epd = EPD(trg[n])
        DoActions([
            SetMemory(0x6509B0, SetTo, trg_epd + 111),  # act[1] + 20
            # SetMemory(act[1][n] + 20, SetTo, 0),
            SetDeaths(CurrentPlayer, SetTo, 0, 0),
            SetMemory(0x6509B0, Subtract, 111 - 96),  # act[0] + 24
            SetDeaths(CurrentPlayer, SetTo, 0x092D0000, 0),
            SetMemory(0x6509B0, Subtract, 96 - 4),  # con[0] + 8
            SetMemory(cp[0][n] + 20, SetTo, EPD(_end)),
            SetMemory(cp[1][n] + 20, SetTo, 0),
            SetMemory(cp[2][n] + 20, SetTo, 0),
            SetMemory(act[3][n] + 16, SetTo, trg_epd + 87),  # act[2] + 20
            SetMemory(act[4][n] + 16, SetTo, trg_epd + 87),
            SetMemory(act[4][n] + 20, SetTo, _end)])
        if EUDIf()(nmod <= 3):  # 1~2 vs 7,4 / 5~6 vs 3,0
            DoActions([
                [SetMemory(con[1 + t][n] + 12, SetTo, 0x17000000)
                 for t in range(4)],  # Never()
                # SetMemory(con[0][n] + 8, SetTo, 0x20073A00 +
                #           f_bread(idptr + idlen - 1)),
                SetDeaths(CurrentPlayer, SetTo, 0x20073A00 +
                          f_bread(idptr + idlen - 1), 0),
                SetMemory(0x6509B0, Add, 95 - 4),  # act[0] + 20
                # SetMemory(act[0][n] + 20, SetTo, (0x2007 - 0x0720) * 0x10000)
                SetDeaths(CurrentPlayer, SetTo,
                          (0x2007 - 0x0720) * 0x10000, 0),
                SetMemory(0x6509B0, Subtract, 95 - 4),  # con[0] + 8
                SetMemory(cp[1][n] + 20, SetTo, 1),
                SetMemory(cp[2][n] + 20, SetTo, 1)])
            if EUDIf()(nmod % 2 == 0):
                DoActions([
                    # SetMemory(con[0][n] + 8, SetTo, 0x073A0000 +
                    #           f_wread(idptr + idlen - 2)),
                    SetDeaths(CurrentPlayer, SetTo, 0x073A0000 +
                              f_wread(idptr + idlen - 2), 0),
                    SetMemory(0x6509B0, Add, 111 - 4),  # act[1] + 20
                    # SetMemory(act[1][n] + 20, SetTo, 0x20 - 0x07)
                    SetDeaths(CurrentPlayer, SetTo, 0x20 - 0x07, 0),
                    SetMemory(0x6509B0, Subtract, 111 - 95),  # act[0] + 20
                    # SetMemory(act[0][n] + 20, SetTo,
                    #           (0x20 - 0x07) * 0x1000000),
                    SetDeaths(CurrentPlayer, SetTo,
                              (0x20 - 0x07) * 0x1000000, 0),
                    SetMemory(0x6509B0, Add, 1),  # act[0] + 24
                    # f_bwrite(act[0][n] + 27, 8)
                    SetDeaths(CurrentPlayer, Subtract, 0x01000000, 0)])
            EUDEndIf()
        if EUDElse()():
            DoActions([
                [SetMemory(con[1 + t][n] + 12, SetTo, 0x16000000)
                 for t in range(2)],  # Always()
                # SetMemory(con[0][n] + 8, SetTo, 0x20073A),
                SetDeaths(CurrentPlayer, SetTo, 0x20073A, 0),
                SetMemory(0x6509B0, Add, 95 - 4),  # act[0] + 20
                # SetMemory(act[0][n] + 20, SetTo, (0x2007 - 0x0720) * 0x100)
                SetDeaths(CurrentPlayer, SetTo, (0x2007 - 0x0720) * 0x100, 0),
                SetMemory(0x6509B0, Subtract, 95 - 4)])  # con[0] + 8])
            if EUDIf()(nmod % 2 == 1):
                DoActions([
                    [SetMemory(con[3 + t][n] + 12, SetTo, 0x16000000)
                     for t in range(2)],  # Always()
                    # SetMemory(con[0][n] + 8, SetTo, 0x2007),
                    SetDeaths(CurrentPlayer, SetTo, 0x2007, 0),
                    SetMemory(0x6509B0, Add, 95 - 4),  # act[0] + 20
                    # SetMemory(act[0][n] + 20, SetTo, 0x2007 - 0x0720)
                    SetDeaths(CurrentPlayer, SetTo, 0x2007 - 0x0720, 0),
                ])
            EUDEndIf()
        EUDEndIf()


def onPluginStart():
    f_init()


@EUDFunc
def f_chatcmp():
    chatlen = f_strlen(chatptr)
    if lenAddr >= 1:
        DoActions(SetMemory(lenAddr, SetTo, chatlen))
    if EUDIf()([chatlen >= minlen, chatlen <= maxlen]):
        t = EUDArray.cast(chatDict[chatlen - minlen])
        if EUDIf()(t >= 1):
            n = t[0]
            i = EUDVariable()
            i << 1
            if EUDWhile()(i <= n):
                if EUDIf()(f_strcmp(chatptr, t[i]) == 0):
                    DoActions(SetMemory(Addr, SetTo, t[n+i]))
                    EUDJump(exit)
                EUDEndIf()
                i += 1
            EUDEndWhile()
        EUDEndIf()
    EUDEndIf()
    if ptrAddr >= 1:
        DoActions(SetMemory(ptrAddr, SetTo, chatptr))
    if rListlen >= 1:
        for i in EUDLoopRange(rListlen):
            subArray = EUDArray.cast(rList[i])
            if EUDIf()(f_memcmp(chatptr, subArray[0], subArray[4]) == 0):
                endlen = subArray[5]
                if EUDIf()(f_memcmp(chatptr + chatlen - endlen, subArray[2], endlen) == 0):
                    if EUDIfNot()(f_strnstr(chatptr, subArray[1], chatlen) == -1):
                        DoActions(SetMemory(patternAddr, SetTo, subArray[3]))
                        EUDJump(exit)
                    EUDEndIf()
                EUDEndIf()
            EUDEndIf()


temp = EUDVariable()
chatDetected = Forward()


def chatEvent(n):
    DoActions([
        cp[0][n] << SetMemoryEPD(EPD(0x6509B0), SetTo, 0),
        act[4][n] << SetMemoryEPD(EPD(0x640B60), SetTo, 0)
    ])
    if EUDLoopN()(6 - n):
        temp << 0

        for t in range(2):
            if EUDIf()(con[1 + 2 * t][n] << Never()):
                for k in range(7, -1, -1):
                    amount = 2 ** (k + 24 - 8 * t)
                    RawTrigger(
                        conditions=Deaths(CurrentPlayer, AtLeast, amount, 0),
                        actions=[
                            SetDeaths(CurrentPlayer, Subtract, amount, 0),
                            temp.AddNumber(amount)
                        ])
            EUDEndIf()

        DoActions(cp[1][n] << SetMemoryEPD(EPD(0x6509B0), Subtract, 0))

        trg[n] << RawTrigger(
            conditions=Deaths(CurrentPlayer, Exactly, 0, 0),  # con[0][n]
            actions=[
                chatptr.SetNumber(0),  # act[2][n]
                SetDeaths(CurrentPlayer, Subtract, 0, 0),  # act[0][n]
                SetMemoryEPD(EPD(0x6509B0), Add, 1),
                SetDeaths(CurrentPlayer, Subtract, 0, 0),  # act[1][n]
                SetMemoryEPD(EPD(0x6509B0), Subtract, 1)
            ])

        DoActions(cp[2][n] << SetMemoryEPD(EPD(0x6509B0), Add, 0))

        for t in range(2):
            if EUDIf()(con[2 + 2 * t][n] << Never()):
                for k in range(7, -1, -1):
                    amount = 2 ** (k + 24 - 8 * t)
                    RawTrigger(
                        conditions=temp.AtLeast(amount),
                        actions=[
                            SetDeaths(CurrentPlayer, Add, amount, 0),
                            temp.SubtractNumber(amount)
                        ])
            EUDEndIf()
        EUDJumpIf(chatptr.AtLeast(1), chatDetected)
        DoActions([
            SetMemoryEPD(EPD(0x6509B0), Add, 109),
            act[3][n] << SetMemoryEPD(EPD(0x640B60), Add, 436),
        ])
    EUDEndLoopN()


def beforeTriggerExec():
    if EUDIf()(Memory(Addr, Exactly, -1)):
        f_init()
    EUDEndIf()

    DoActions(SetMemory(Addr, SetTo, 0))  # 초기화
    if rListlen >= 1:
        DoActions(SetMemory(patternAddr, SetTo, 0))
    chatptr << 0

    oldcp = f_getcurpl()

    for n in range(2):
        chatEvent(n)

    if EUDIf()(Never()):
        chatDetected << NextTrigger()
        DoActions(SetMemory(Addr, SetTo, 1))
        f_chatcmp()
    EUDEndIf()

    exit << NextTrigger()
    f_setcurpl(oldcp)
