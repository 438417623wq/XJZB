"""Literal port of blast.c (Mark Adler) for byte-exact comparison."""
MAXBITS = 13
MAXWIN = 4096


class State:
    def __init__(self, data):
        self.d = data
        self.inpos = 0
        self.bitbuf = 0
        self.bitcnt = 0
        self.out = bytearray()
        self.next = 0
        self.first = 1

    def bits(self, need):
        val = self.bitbuf
        while self.bitcnt < need:
            if self.inpos >= len(self.d):
                raise EOFError
            val |= self.d[self.inpos] << self.bitcnt
            self.inpos += 1
            self.bitcnt += 8
        self.bitbuf = val >> need
        self.bitcnt -= need
        return val & ((1 << need) - 1)


LITLEN = [11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8,
          9, 7, 6, 7, 8, 7, 6, 55, 8, 23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5,
          7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12,
          8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27,
          44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45,
          44, 173]
LENLEN = [2, 35, 36, 53, 38, 23]
DISTLEN = [2, 20, 53, 230, 247, 151, 248]
BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]


class Huff:
    def __init__(self, rep):
        length = []
        for b in rep:
            left = (b >> 4) + 1
            ln = b & 15
            length.extend([ln] * left)
        n = len(length)
        count = [0] * (MAXBITS + 1)
        for ln in length:
            count[ln] += 1
        offs = [0] * (MAXBITS + 1)
        for ln in range(1, MAXBITS):
            offs[ln + 1] = offs[ln] + count[ln]
        symbol = [0] * n
        for sym in range(n):
            if length[sym] != 0:
                symbol[offs[length[sym]]] = sym
                offs[length[sym]] += 1
        self.count = count
        self.symbol = symbol


LITCODE = Huff(LITLEN)
LENCODE = Huff(LENLEN)
DISTCODE = Huff(DISTLEN)


def decode(s, h):
    bitbuf = s.bitbuf
    left = s.bitcnt
    code = first = index = 0
    ln = 1
    nxt = 1
    while True:
        while left:
            left -= 1
            code |= (bitbuf & 1) ^ 1
            bitbuf >>= 1
            count = h.count[nxt]
            nxt += 1
            if code < first + count:
                s.bitbuf = bitbuf
                s.bitcnt = (s.bitcnt - ln) & 7
                return h.symbol[index + (code - first)]
            index += count
            first += count
            first <<= 1
            code <<= 1
            ln += 1
        left = (MAXBITS + 1) - ln
        if left == 0:
            break
        if s.inpos >= len(s.d):
            raise EOFError
        bitbuf = s.d[s.inpos]
        s.inpos += 1
        if left > 8:
            left = 8
    return -9


def decomp(s):
    lit = s.bits(8)
    if lit > 1:
        return -1
    dic = s.bits(8)
    if dic < 4 or dic > 6:
        return -2
    while True:
        if s.bits(1):
            symbol = decode(s, LENCODE)
            ln = BASE[symbol] + s.bits(EXTRA[symbol])
            if ln == 519:
                break
            symbol = 2 if ln == 2 else dic
            dist = decode(s, DISTCODE) << symbol
            dist += s.bits(symbol)
            dist += 1
            if s.first and dist > s.next:
                return -3
            while ln:
                to = s.next
                frm = to - dist
                cp = MAXWIN
                if s.next < dist:
                    frm += cp
                    cp = dist
                cp -= s.next
                if cp > ln:
                    cp = ln
                ln -= cp
                s.next += cp
                while cp:
                    s.out.append(s.out[frm])
                    frm += 1
                    cp -= 1
                if s.next == MAXWIN:
                    s.next = 0
                    s.first = 0
        else:
            symbol = decode(s, LITCODE) if lit else s.bits(8)
            s.out.append(symbol)
            s.next += 1
            if s.next == MAXWIN:
                s.next = 0
                s.first = 0
    return 0


def blast(data):
    s = State(data)
    err = decomp(s)
    return bytes(s.out), err, s.bitcnt, s.inpos
