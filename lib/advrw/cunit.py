def CUnit(i):
    if i == 0:
        return 0x59CCA8
    else:
        return 0x628298 - 0x150 * (i - 1)


def CImage(i):
    return 0x57D728 - 0x40 * i


def CSprite(i):
    return 0x63FD04 - 0x24 * i
