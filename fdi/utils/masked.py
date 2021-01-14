
def masked(value, mask):
    """ Returns the masked part of the value, high bit number of mask, how wide.

    e.g. value=0b00101100 mask=0b00011100, the result is 0b011, 5, 3
    """
    shift = 0
    m = mask
    # count how many 0s on the right side
    while (m & 1) == 0 and shift <= 64:
        m >>= 1
        shift += 1
    v = (value & mask) >> shift
    # get the width of the mask
    wide = 0
    while m:
        m >>= 1
        wide += 1
    return v, shift+wide, wide
