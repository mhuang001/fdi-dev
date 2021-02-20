
def masked(value, mask):
    """ Returns the masked part of the value, high bit number of mask, how wide the mask is..

    e.g. value=0b00101100 mask=0b00011100, the result is 0b011, 5, 3
    """

    mask_height = mask.bit_length()
    right0s = 0
    m = mask
    # count how many 0s on the right side
    while (m & 1) == 0 and right0s <= 64:
        m >>= 1
        right0s += 1
    v = (value & mask) >> right0s
    # get the width of the mask
    mask_width = mask_height - right0s
    return v, mask_height, mask_width
