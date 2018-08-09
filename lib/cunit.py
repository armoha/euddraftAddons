from safecuniti import (
    f_dwepdcunitread_epd_safe,
    f_dwcunitread_epd_safe,
    f_epdcunitread_epd_safe
)
from safecunitcpi import (
    f_dwepdcunitread_cp_safe,
    f_dwcunitread_cp_safe,
    f_epdcunitread_cp_safe
)
from cunitepdi import (
    f_dwepdcunitread_epd,
    f_dwcunitread_epd,
    f_epdcunitread_epd
)
from cunitcpi import (
    f_dwepdcunitread_cp,
    f_dwcunitread_cp,
    f_epdcunitread_cp
)


def CUnit(i):
	if i == 0:
		return 0x59CCA8
	else:
		return 0x628298 - 0x150 * (i-1)


def CImage(i):
	return 0x57D728 - 0x40 * i


def CSprite(i):
	return 0x63FD04 - 0x24 * i
