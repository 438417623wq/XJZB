"""Find which listfile name's key actually decrypts a given block.

For single-sector entries there is no offset table to validate against, so we
test every known filename as a key source and accept the one whose decrypted
stream begins with a valid PKWARE literal-mode byte (0 or 1).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive as S  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def main():
    target_blocks = [22, 27, 58, 64]   # failing shadow/glow entries
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        lf = [n for n in a.read("(listfile)").decode("latin-1")
              .replace("\r", "\n").split("\n") if n.strip()]
        print("names: %d" % len(lf))

        names_forms = []
        for n in lf:
            names_forms.append(n.split("\\")[-1])
            names_forms.append(n)
        names_forms = list(dict.fromkeys(names_forms))
        print("key-name candidates: %d" % len(names_forms))

        for blk in target_blocks:
            o, cs, fs, flags, rel = a.block_table[blk]
            a.fp.seek(o)
            raw = a.fp.read(cs)
            print("\n== blk%d cs=%d fs=%d rel=%d" % (blk, cs, fs, rel))
            found = []
            for kn in names_forms:
                base = S.hash_string(kn, S.HASH_FILE_KEY)
                for label, key in (("base", base),
                                   ("^fs", ((base + rel) ^ fs) & 0xFFFFFFFF),
                                   ("^cs", ((base + rel) ^ cs) & 0xFFFFFFFF)):
                    d = S.decrypt(raw, key)
                    if d and d[0] in (0, 1):
                        found.append((kn, label, key, d[0]))
            if found:
                for kn, label, key, fb in found[:6]:
                    print("   HIT %-34s %-5s key=0x%08X first=%d" % (kn, label, key, fb))
            else:
                print("   no candidate name decrypts this block")


if __name__ == "__main__":
    main()
