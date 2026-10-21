"""v2.11: parse scripts\\iscript.bin to get AUTHORITATIVE animation frame counts.

The walk length is not guessable from pixels: every walk block is a distinct
pose, so no self-similarity / periodicity / coverage test can find the seam
(probe_v211bn/bo/bs/bt all failed even on marine, whose walk=3 is known).

iscript.bin is the animation script the engine actually runs, so it is the
ground truth. StarDat's copy starts with a flat (u16 id, u16 offset) pair list
(198,7420),(199,7580),(200,8492),...  -- patch_rt/BrooDat's copies start with
e6 97 00 00 (a compressed/obfuscated blob) and are unusable.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"

# opcode -> number of u16 parameters
ARITY = {
    0x00: 1, 0x01: 1, 0x02: 1, 0x03: 1, 0x04: 1, 0x05: 1, 0x06: 2,
    0x07: 1, 0x08: 2, 0x09: 2, 0x0A: 1, 0x0B: 1, 0x0C: 0, 0x0D: 1,
    0x0E: 0, 0x0F: 0, 0x10: 1, 0x11: 1, 0x12: 1, 0x13: 1, 0x14: 0,
    0x15: 0, 0x16: 1, 0x17: 1, 0x18: 0, 0x19: 0, 0x1A: 0, 0x1B: 1,
    0x1C: 1, 0x1D: 0, 0x1E: 0, 0x1F: 0, 0x20: 0, 0x21: 0, 0x22: 0,
    0x23: 0, 0x24: 0, 0x25: 0, 0x26: 0, 0x27: 0, 0x28: 0, 0x29: 0,
    0x2A: 0, 0x2B: 0, 0x2C: 0, 0x2D: 0, 0x2E: 0, 0x2F: 0, 0x30: 0,
    0x31: 0, 0x32: 0, 0x33: 0, 0x34: 0, 0x35: 0, 0x36: 0, 0x37: 0,
    0x38: 0, 0x39: 0, 0x3A: 0, 0x3B: 0, 0x3C: 0, 0x3D: 0, 0x3E: 0,
    0x3F: 0,
}
END = 0x40

ANIM = {0x00: "Init", 0x01: "Death", 0x02: "GndAttkInit", 0x03: "AirAttkInit",
        0x04: "Unused1", 0x05: "GndAttkRpt", 0x06: "AirAttkRpt",
        0x07: "CastSpell", 0x08: "GndAttkToIdle", 0x09: "AirAttkToIdle",
        0x0A: "Unused2", 0x0B: "Walking", 0x0C: "WalkingToIdle",
        0x0D: "SpecialState1", 0x0E: "SpecialState2", 0x0F: "AlmostBuilt",
        0x10: "Built", 0x11: "Landing", 0x12: "LiftOff", 0x13: "IsWorking",
        0x14: "WorkingToIdle", 0x15: "WarpIn", 0x16: "Unused3", 0x17: "InitTurret",
        0x18: "Unused4", 0x19: "Unused5", 0x1A: "Unused6", 0x1B: "Unused7",
        0x1C: "Unused8", 0x1D: "Unused9", 0x1E: "Unused10"}


def parse_types(data):
    """Flat (u16 id, u16 offset) pair list from offset 0."""
    pairs = []
    o = 0
    while o + 4 <= len(data):
        tid = struct.unpack_from("<H", data, o)[0]
        toff = struct.unpack_from("<H", data, o + 2)[0]
        if tid == 0xFFFF or toff == 0xFFFF:
            break
        if toff >= len(data):
            break
        pairs.append((tid, toff))
        o += 4
    return pairs


def parse_anims(data, off):
    """(u16 animId, u16 offset) pair list until 0xFFFF."""
    out = []
    o = off
    while o + 4 <= len(data):
        aid = struct.unpack_from("<H", data, o)[0]
        aoff = struct.unpack_from("<H", data, o + 2)[0]
        if aid == 0xFFFF or aoff == 0xFFFF:
            break
        if aoff >= len(data):
            break
        out.append((aid, aoff))
        o += 4
    return out


def parse_ops(data, start, limit):
    """Decode opcodes; return (ops, ok) where ok means we ended exactly."""
    ops = []
    o = start
    while o + 2 <= limit:
        op = struct.unpack_from("<H", data, o)[0]
        o += 2
        if op == END:
            ops.append((END, None))
            return ops, (o == limit)
        n = ARITY.get(op)
        if n is None:
            return ops, False
        args = []
        for _ in range(n):
            if o + 2 > limit:
                return ops, False
            args.append(struct.unpack_from("<H", data, o)[0])
            o += 2
        ops.append((op, args))
    return ops, False


ar = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
data, gaps = ar.read_with_gaps("scripts\\iscript.bin")
print("StarDat iscript.bin bytes=%d gaps=%d" % (len(data), len(gaps)))

pairs = parse_types(data)
print("type pairs=%d  id range %d..%d" % (len(pairs), min(p[0] for p in pairs),
                                          max(p[0] for p in pairs)))
print("first 20 ids:", [p[0] for p in pairs[:20]])
print("last 10 ids:", [p[0] for p in pairs[-10:]])

# validate the opcode table on the very first type
tid0, toff0 = pairs[0]
anims = parse_anims(data, toff0)
print("\ntype %d @%d  anims=%d" % (tid0, toff0, len(anims)))
okc = 0
for i, (aid, aoff) in enumerate(anims):
    limit = anims[i + 1][1] if i + 1 < len(anims) else aoff + 400
    ops, ok = parse_ops(data, aoff, min(limit, len(data)))
    okc += 1 if ok else 0
    frames = [a[0] for op, a in ops if op == 0x00]
    print("   anim %-14s @%-6d ops=%-3d ok=%-5s playfram=%s"
          % (ANIM.get(aid, "0x%02x" % aid), aoff, len(ops), ok, frames[:24]))
print("   clean parses: %d/%d" % (okc, len(anims)))
ar.close()
