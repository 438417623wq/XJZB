"""Round-trip self-test for the FGK huffman port: compress then decompress."""
import random
import mphuff


class _Out:
    def __init__(self):
        self.buf = bytearray()
        self.bitbuf = 0
        self.bitcnt = 0

    def put(self, value, nbits):
        self.bitbuf |= (value << self.bitcnt) & 0xFFFFFFFF
        self.bitcnt += nbits
        while self.bitcnt >= 8:
            self.buf.append(self.bitbuf & 0xFF)
            self.bitbuf >>= 8
            self.bitcnt -= 8

    def flush(self):
        while self.bitcnt:
            self.buf.append(self.bitbuf & 0xFF)
            self.bitbuf >>= 8
            self.bitcnt -= 8 if self.bitcnt > 8 else self.bitcnt


def compress(data, dtype):
    """Mirror of StormLib Compress(): adaptive huffman, DataType written first."""
    tree = mphuff.HuffTree()
    tree.build(mphuff.TABLES[dtype])
    sparse = dtype == 1
    os_ = _Out()
    os_.put(dtype, 8)

    def encode(item):
        bits = 0
        bitbuf = 0
        p = item.parent
        while p is not None:
            bitbuf = (bitbuf << 1) | (0 if p.child_lo is item else 1)
            bits += 1
            item2 = p
            # climb: current node's relation to its parent determines the bit
            p = p.parent
            item = item2
        # wait: relation must be evaluated per level, redo below
        raise RuntimeError

    # proper encode: walk leaf->root collecting whether node is parent's child_lo
    def encode2(leaf):
        bits = 0
        bitbuf = 0
        node = leaf
        while node.parent is not None:
            par = node.parent
            bitbuf = (bitbuf << 1) | (0 if par.child_lo is node else 1)
            bits += 1
            node = par
        return bitbuf, bits

    for b in data:
        item = tree.items_by_byte[b]
        if item is None:
            # NYT escape
            bitbuf, bits = encode2(tree.items_by_byte[0x101])
            os_.put(bitbuf, bits)
            os_.put(b, 8)
            tree.insert_new_branch(tree.s.prev.val, b)
            tree.inc_weights(tree.items_by_byte[b])
        else:
            bitbuf, bits = encode2(item)
            os_.put(bitbuf, bits)
            if sparse:
                tree.inc_weights(item)
    bitbuf, bits = encode2(tree.items_by_byte[0x100])
    os_.put(bitbuf, bits)
    os_.flush()
    return bytes(os_.buf)


def main():
    rng = random.Random(42)
    cases = []
    cases.append(bytes(rng.randrange(0, 4) for _ in range(1000)))          # tiny alphabet
    cases.append(bytes(rng.randrange(0, 256) for _ in range(2048)))        # uniform
    cases.append(b"A" * 500 + bytes(rng.randrange(0, 8) for _ in range(500)))
    pal = bytearray()
    for i in range(256):
        pal += bytes([i, i, i, 0])
    cases.append(bytes(pal))                                               # palette-like
    for dtype in (1, 2, 4):
        for c in cases:
            enc = compress(c, dtype)
            dec = mphuff.decompress(enc, len(c))
            ok = dec == c
            print("dtype=%d len=%4d enc=%5d %s" % (dtype, len(c), len(enc), "OK" if ok else "MISMATCH"))
            if not ok:
                for i, (a, b) in enumerate(zip(c, dec)):
                    if a != b:
                        print("  first diff at", i, a, b)
                        break
                return


main()
