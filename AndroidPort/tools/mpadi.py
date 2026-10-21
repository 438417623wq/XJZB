"""MPQ ADI-mono decompressor — port of StormLib adpcm.cpp DecompressADPCM."""

NEXT_STEP = [-1, 0, -1, 4, -1, 2, -1, 6, -1, 1, -1, 5, -1, 3, -1, 7,
             -1, 1, -1, 5, -1, 3, -1, 7, -1, 2, -1, 4, -1, 6, -1, 8]
STEP_SIZE = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
             34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143,
             157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658,
             724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024,
             3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
             15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767]
INITIAL_STEP = 0x2C


def _decode_sample(pred, enc, step_size, diff):
    if enc & 0x01:
        diff += step_size >> 0
    if enc & 0x02:
        diff += step_size >> 1
    if enc & 0x04:
        diff += step_size >> 2
    if enc & 0x08:
        diff += step_size >> 3
    if enc & 0x10:
        diff += step_size >> 4
    if enc & 0x20:
        diff += step_size >> 5
    if enc & 0x40:
        pred -= diff
        if pred <= -32768:
            pred = -32768
    else:
        pred += diff
        if pred >= 32767:
            pred = 32767
    return pred


def decompress_adi_mono(data, out_len):
    """ChannelCount = 1."""
    pos = 0
    out = bytearray()

    def rd():
        nonlocal pos
        if pos >= len(data):
            return None
        b = data[pos]
        pos += 1
        return b

    def wr16(v):
        out.append(v & 0xFF)
        out.append((v >> 8) & 0xFF)

    rd()                     # first byte always zero
    bit_shift = rd()         # bit shift (level - 1)

    predicted = 0
    step_index = INITIAL_STEP

    init = rd()
    if init is None:
        return bytes(out)
    lo = rd()
    init = init | (lo << 8)
    if init >= 0x8000:
        init -= 0x10000
    predicted = init
    wr16(init & 0xFFFF)

    while True:
        enc = rd()
        if enc is None:
            break
        if enc == 0x80:
            if step_index != 0:
                step_index -= 1
            wr16(predicted & 0xFFFF)
        elif enc == 0x81:
            step_index += 8
            if step_index > 0x58:
                step_index = 0x58
        else:
            step_size = STEP_SIZE[step_index]
            predicted = _decode_sample(predicted, enc, step_size, step_size >> bit_shift)
            wr16(predicted & 0xFFFF)
            step_index += NEXT_STEP[enc & 0x1F]
            if step_index < 0:
                step_index = 0
            elif step_index > 88:
                step_index = 88
        if len(out) >= out_len:
            break
    return bytes(out[:out_len])
