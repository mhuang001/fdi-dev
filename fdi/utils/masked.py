
def masked(value, mask):
    """ Returns the masked part of the value.

    e.g. value=0b00101100 mask=0b00011100, the result is 0b011
    """
    shift = 0
    m = mask
    # count how many 0s on the right side
    while (m % 2) == 0 and shift <= 64:
        m >>= 1
        shift += 1
    v = (value & mask) >> shift
    return v
