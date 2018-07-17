from eudplib import *
import re
'''[인덱스고정]
인덱스번호 : 유닛, 장소, 플레이어
인덱스번호, SetMemoryEPD(epd + 0xDC // 4, Add, 0x800000)'''
Trg = []
Acts = ['' for _ in range(1700)]


def Index2CUnit(index):  # index를 해당하는 구조오프셋 주소로 바꿉니다.
    if index == 0:
        return 0x59CCA8
    else:
        return 0x628298 - 0x150 * (index - 1)


def EncPlayer(player):
    pDict = {'P1': 0, 'P2': 1, 'P3': 2, 'P4': 3,
             'P5': 4, 'P6': 5, 'P7': 6, 'P8': 7}
    try:
        ret = pDict[player]
    except KeyError:
        return player
    else:
        return ret


def onInit():
    for key, value in settings.items():
        try:
            Index = int(key)
        except (ValueError):
            p_k = re.compile('^\d+')
            p_v = re.compile('(?<=\d,).+')
            IndexNum = int(p_k.findall(key)[0])
            Actions = p_v.findall(key)[0]
            Acts[IndexNum] += Actions
            print('추가액션({}):{}'.format(IndexNum, Actions))
        else:
            Trg.append((Index, value))  # Trg[n] = ('Actions', Index)
            print('{}({}): {}'.format(hex(Index2CUnit(Index)), Index, value))
    Trg.sort(reverse=True)
    print('Address(index): Unit, Location, Player')


onInit()


def afterTriggerExec():
    for Index, Act in Trg:  # n이 인덱스 번호
        A = Act.split(',')
        unit = int(EncodeUnit(A[0].strip()))
        loc = int(EncodeLocation(A[1].strip()))
        player = int(EncPlayer(A[2].strip()))
        ptr = Index2CUnit(Index)
        epd = EPD(ptr)
        # Index의 유닛타입이 .edd와 일치하지 않는 경우 RemoveTimer를 1로
        if EUDIfNot()(MemoryEPD(epd + 0x64 // 4, Exactly, unit)):
            DoActions(SetMemoryEPD(epd + 0x110 // 4, SetTo, 1))
        EUDEndIf()
        # ---------------------------------------------------------------------
        # Index유닛이 존재하지 않는 경우
        if EUDIf()([
            MemoryEPD(epd + 0xC // 4, Exactly, 0),
            Memory(0x6283F0, AtMost, 1698)  # 캔낫이 아님.
        ]):
            if EUDIf()(Memory(0x628438, Exactly, ptr)):  # 유닛 생성
                DoActions(CreateUnit(1, unit, loc, player))
            if EUDElse()():
                temp = f_dwread_epd(EPD(0x628438))
                DoActions([
                    SetMemory(0x628438, SetTo, ptr),
                    CreateUnit(1, unit, loc, player),
                    SetMemory(0x628438, SetTo, temp)
                ])
            EUDEndIf()
            if Acts[Index] is not '':
                if EUDIf()(MemoryEPD(epd + 0x64 // 4, Exactly, unit)):
                    try:
                        DoActions([eval(Acts[Index])])
                    except SyntaxError:
                        print('SyntaxError:{}'.format(Acts[Index]))
                        pass
                EUDEndIf()
        EUDEndIf()
