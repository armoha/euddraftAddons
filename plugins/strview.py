from eudplib import *
import struct
from operator import itemgetter


chkt = GetChkTokenized()
STR = bytearray(chkt.getsection('STR'))


def hex2int(hex):
    return int("0x%04X" % struct.unpack("<H", hex), 0)


def stroffset(n):
    return hex2int(STR[2 * (n + 1):2 * (n + 2)])


def addr2str(s, pos):
    end = s.find(b'\0', pos + 1)
    if end != -1:
        return s[pos:end]
    else:
        return s[pos:]


STR_usage, STR_no, STR_start = 0, hex2int(STR[0:2]), hex2int(STR[2:4])
STR_output = []

for n in range(STR_no):
    strlen = min(stroffset(n + 1), 65535) - stroffset(n)
    if stroffset(n) == STR_no * 2 + 2:
        last_str = addr2str(STR, stroffset(n))
        if len(last_str) > 1:
            STR_output.append(
                [n + 1, len(last_str), last_str.decode("cp949")])
            STR_usage += 1
    elif strlen > 0:
        STR_output.append(
            [n + 1, strlen, STR[stroffset(n):stroffset(n + 1)].decode("cp949")])
        STR_usage += 1

STR_output.sort(key=itemgetter(1), reverse=True)

print('스트링 개수: %d/%d, 시작 위치: %d' % (STR_usage, STR_no, STR_start))

f = open('string_analysis.txt', 'w')
f.write('스트링 번호, 길이, 내용물\n')
f.write('\n'.join(map(str, STR_output)))
f.close()
