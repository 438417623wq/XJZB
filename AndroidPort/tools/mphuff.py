"""MPQ adaptive (FGK) Huffman decoder — faithful port of StormLib huffman.cpp
decompression path, minus the QuickLinks speed optimisation.

Payload: first 8 bits = DataType, then the FGK bitstream.
"""


def _tbl(hexlines):
    return bytes.fromhex("".join(hexlines.split()))


_SPARSE = _tbl("""
0A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 02
00 00
""")

_BINARY = _tbl("""
54 16 16 0D 0C 08 06 05 06 05 06 03 04 04 03 05
0E 0B 14 13 13 09 0B 06 05 04 03 02 03 02 02 02
0D 07 09 06 06 04 03 02 04 03 03 03 03 03 02 02
09 06 04 04 04 04 03 02 03 02 02 02 02 03 02 04
08 03 04 07 09 05 03 03 03 03 02 02 02 03 02 02
03 02 02 02 02 02 02 02 02 01 01 01 02 01 02 02
06 0A 08 08 06 07 04 03 04 04 02 02 04 02 03 03
04 03 07 07 09 06 04 03 03 02 01 02 02 02 02 02
0A 02 02 03 02 02 01 01 02 02 02 06 03 05 02 03
02 01 01 01 01 01 01 01 01 01 01 02 03 01 01 01
02 01 01 01 01 01 01 02 04 04 04 07 09 08 0C 02
01 01 01 01 01 01 01 01 01 01 01 01 02 01 01 03
04 01 02 04 05 01 01 01 01 01 01 01 02 01 01 01
04 01 01 01 01 01 02 01 01 01 01 01 01 01 01 01
02 01 01 01 01 01 01 01 03 01 01 01 01 01 01 01
02 01 01 01 01 01 01 02 02 01 01 02 02 02 06 4B
00 00
""")

_TEXT = _tbl("""
00 00 00 00 00 00 00 00 00 03 27 00 00 23 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
FF 01 01 01 01 01 01 01 02 02 01 01 06 0E 10 04
06 08 05 04 04 03 03 02 02 03 03 01 01 02 01 01
01 04 02 04 02 02 02 01 01 04 01 01 02 03 03 02
03 01 03 06 04 01 01 01 01 01 01 02 01 02 01 01
01 29 07 16 12 40 0A 0A 11 25 01 03 17 10 26 2A
10 01 23 23 2F 10 06 07 02 09 01 01 01 01 01 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
""")

_GENERAL = _tbl("""
FF 0B 07 05 0B 02 02 02 06 02 02 01 04 02 01 03
09 01 01 01 03 04 01 01 02 01 01 01 02 01 01 01
05 01 01 01 0D 01 01 01 01 01 01 01 01 01 01 01
02 01 01 03 01 01 01 01 01 01 01 02 01 01 01 01
0A 04 02 01 06 03 02 01 01 01 01 01 03 01 01 01
05 02 03 04 03 03 03 02 01 01 01 02 01 02 03 03
01 03 01 01 02 05 01 01 04 03 05 01 03 01 03 03
02 01 04 03 0A 06 01 01 01 01 01 01 01 01 01 01
02 02 01 0A 02 05 01 01 02 07 02 17 01 05 01 01
0E 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01
01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01
01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01
06 02 01 04 05 01 01 02 01 01 01 01 02 01 01 01
01 01 01 01 01 01 01 01 01 01 01 01 01 01 01 01
01 01 01 01 01 01 01 01 07 01 01 02 01 01 01 01
02 01 01 01 01 01 01 01 02 01 01 01 01 01 01 11
00 00
""")

TABLES = {1: _SPARSE, 2: _BINARY, 3: _TEXT, 4: _GENERAL}


class _Item:
    __slots__ = ("val", "weight", "prev", "next", "parent", "child_lo")

    def __init__(self, val, weight):
        self.val = val
        self.weight = weight
        self.prev = self.next = self.parent = self.child_lo = None


class HuffTree:
    """Circular doubly-linked list with a single sentinel: sentinel.next is the
    highest-weight item (decode root), sentinel.prev the lowest."""

    def __init__(self):
        self.s = _Item(-1, 0)
        self.s.next = self.s.prev = self.s
        self.items_by_byte = [None] * 0x102

    def _link_after(self, ref, item):
        item.next = ref.next
        item.prev = ref.next.prev
        ref.next.prev = item
        ref.next = item

    def _remove(self, item):
        item.next.prev = item.prev
        item.prev.next = item.next
        item.next = item.prev = None

    def _find_ge(self, start, weight):
        p = start
        while p is not self.s:
            if p.weight >= weight:
                return p
            p = p.prev
        return self.s

    def _fixup(self, item, max_weight):
        if item.weight < max_weight:
            higher = self._find_ge(self.s.prev, item.weight)
            self._remove(item)
            self._link_after(higher, item)
        else:
            max_weight = item.weight
        return max_weight

    def build(self, dist):
        s = self.s
        s.next = s.prev = s
        self.items_by_byte = [None] * 0x102
        max_w = 0
        for i in range(0x100):
            if dist[i]:
                it = _Item(i, dist[i])
                self.items_by_byte[i] = it
                self._link_after(s, it)             # InsertAfter + NULL point = front
                max_w = self._fixup(it, max_w)
        for v in (0x100, 0x101):                    # termination + NYT at the end
            it = _Item(v, 1)
            self.items_by_byte[v] = it
            self._link_after(s.prev, it)            # InsertBefore + NULL point = end
        lo = s.prev
        while lo is not s:
            hi = lo.prev
            if hi is s:
                break
            parent = _Item(0, hi.weight + lo.weight)
            self._link_after(s, parent)
            lo.parent = parent
            hi.parent = parent
            parent.child_lo = lo
            max_w = self._fixup(parent, max_w)
            lo = hi.prev

    def inc_weights(self, item):
        while item is not None:
            item.weight += 1
            higher = self._find_ge(item.prev, item.weight)
            child_hi = higher.next
            if child_hi is not item:
                self._remove(child_hi)
                self._link_after(item, child_hi)
                self._remove(item)
                self._link_after(higher, item)
                child_lo = child_hi.parent.child_lo
                parent = item.parent
                if parent.child_lo is item:
                    parent.child_lo = child_hi
                if child_lo is child_hi:
                    child_hi.parent.child_lo = item
                parent = item.parent
                item.parent = child_hi.parent
                child_hi.parent = parent
            item = item.parent

    def insert_new_branch(self, v1, v2):
        last = self.s.prev
        hi = _Item(v1, last.weight)
        self._link_after(last, hi)                  # InsertBefore = end
        hi.parent = last
        self.items_by_byte[v1] = hi
        lo = _Item(v2, 0)
        self._link_after(hi, lo)
        lo.parent = last
        last.child_lo = lo
        self.items_by_byte[v2] = lo
        self.inc_weights(lo)


class _Bits:
    __slots__ = ("d", "pos")

    def __init__(self, data):
        self.d = data
        self.pos = 0

    def get8(self):
        p = self.pos >> 3
        if p + 1 >= len(self.d):
            raise EOFError
        sh = self.pos & 7
        b = ((self.d[p] >> sh) | (self.d[p + 1] << (8 - sh))) & 0xFF
        self.pos += 8
        return b

    def get1(self):
        p = self.pos >> 3
        if p >= len(self.d):
            raise EOFError
        b = (self.d[p] >> (self.pos & 7)) & 1
        self.pos += 1
        return b


def decompress(data, out_len):
    """Decode one complete MPQ huffman payload. Returns bytes."""
    bs = _Bits(data)
    dtype = bs.get8()
    dist = TABLES.get(dtype)
    if dist is None:
        raise ValueError("bad huffman data type %d" % dtype)
    sparse = dtype == 1
    tree = HuffTree()
    tree.build(dist)
    out = bytearray()
    while True:
        item = tree.s.next
        while item.child_lo is not None:
            bit = bs.get1()
            item = item.child_lo.prev if bit else item.child_lo
        v = item.val
        if v == 0x100:
            break
        if v == 0x101:
            v = bs.get8()
            tree.insert_new_branch(tree.s.prev.val, v)
            if not sparse:
                tree.inc_weights(tree.items_by_byte[v])
        if len(out) >= out_len:
            break
        out.append(v & 0xFF)
        if sparse:
            tree.inc_weights(tree.items_by_byte[v])
    return bytes(out)
