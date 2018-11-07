from eudplib import GetChkTokenized


def onInit():
    chkt = GetChkTokenized()
    UNIT = chkt.getsection('UNIT')  # placed units
    if len(UNIT) % 36 != 0:
        print("Validation: UNIT section must be a multiple of 36 bytes.")
        return

    count = 0
    newUNIT = bytearray()
    for i in range(0, len(UNIT), 36):
        u = bytearray(UNIT[i:i + 36])
        if u[17] == 100 and u[14] & (1 << 1):
            count += 1
            u[14] = u[14] - (1 << 1)
        if u[18] == 100 and u[14] & (1 << 2):
            u[14] = u[14] - (1 << 2)
        if u[19] == 100 and u[14] & (1 << 3):
            u[14] = u[14] - (1 << 3)
        newUNIT += u
    chkt.setsection('UNIT', newUNIT)
    print("Hit points of %u units are fixed." % count)


onInit()
