"""Sanity-check the hash/block tables of each archive, with and without decryption.

If an archive stores its tables unencrypted, blindly decrypting them scrambles
the entries in a way that can still look superficially plausible.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402

ROOT = r"F:\KF\XJZB"


def read_tables(path, decrypt_tables):
    with open(path, "rb") as fp:
        blob = fp.read(2048)
        off = blob.find(b"MPQ\x1a")
        fp.seek(off)
        (magic, hsize, asize, fmt, shift,
         hpos, bpos, hcount, bcount) = struct.unpack("<4sIIHHIIII", fp.read(32))

        fp.seek(hpos + off)
        hraw = fp.read(hcount * 16)
        fp.seek(bpos + off)
        braw = fp.read(bcount * 16)

    if decrypt_tables:
        hraw = M._decrypt(hraw, M.hash_string("(hash table)", M.HASH_FILE_KEY))
        braw = M._decrypt(braw, M.hash_string("(block table)", M.HASH_FILE_KEY))

    hashes = [struct.unpack_from("<IIHHI", hraw, i * 16) for i in range(hcount)]
    blocks = [struct.unpack_from("<IIII", braw, i * 16) for i in range(bcount)]
    return dict(off=off, fmt=fmt, shift=shift, hpos=hpos, bpos=bpos,
                hcount=hcount, bcount=bcount, asize=asize,
                hashes=hashes, blocks=blocks)


def score(t, filesize):
    hashes, blocks = t["hashes"], t["blocks"]
    n_empty = sum(1 for h in hashes if h[4] == 0xFFFFFFFF)
    # valid block indices referenced from the hash table
    maxbi = 0
    bad_bi = 0
    for h in hashes:
        bi = h[4]
        if bi != 0xFFFFFFFF:
            if bi < t["bcount"]:
                maxbi = max(maxbi, bi)
            else:
                bad_bi += 1

    exists = 0
    total_cs = 0
    sane_space = 0
    for (o, cs, fs, flags) in blocks:
        if flags & M.FLAG_EXISTS:
            exists += 1
            total_cs += cs
            if cs <= fs and o + cs <= filesize:
                sane_space += 1
    return dict(n_empty=n_empty, maxbi=maxbi, bad_bi=bad_bi, exists=exists,
                total_cs=total_cs, sane=sane_space)


def main():
    for arc in ("StarDat.mpq", "BrooDat.mpq", "BroodWar.mpq", "patch_rt.mpq"):
        path = os.path.join(ROOT, arc)
        if not os.path.exists(path):
            continue
        filesize = os.path.getsize(path)
        print("=" * 72)
        print("%s  filesize=%d" % (arc, filesize))
        for dec in (True, False):
            t = read_tables(path, dec)
            s = score(t, filesize)
            print("  decrypt_tables=%-5s  empty=%d/%d  maxBlockIdx=%d badIdx=%d"
                  % (dec, s["n_empty"], t["hcount"], s["maxbi"], s["bad_bi"]))
            print("      exists=%d  sum(csize)=%d  spaceSane=%d/%d"
                  % (s["exists"], s["total_cs"], s["sane"], t["bcount"]))
            print("      first3 hash: %s" % (t["hashes"][:3],))
            print("      first3 blk : %s" % (t["blocks"][:3],))
        print()


if __name__ == "__main__":
    main()
