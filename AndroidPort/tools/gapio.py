"""Gap-aware reader for files extracted from the damaged warez archives.

Each file may be missing a few bytes at known positions (the repacker's DCL
compressor truncated some sectors). The extracted byte stream is the original
with those gaps removed. This reader maps ORIGINAL file positions to extracted
positions, skipping over the gaps, so structured data (u16 arrays, frame
tables...) stays aligned. Bytes inside a gap are unavailable; reads there
return a filler byte.
"""


class GapReader:
    def __init__(self, data, gaps):
        """gaps: list of (orig_pos, size) sorted by orig_pos — original file
        positions where `size` bytes are missing from `data`."""
        self.d = data
        self.gaps = gaps
        # prefix sums: for gap k, cum[k] = total missing bytes before gaps[k]
        self.cum = []
        c = 0
        for pos, size in gaps:
            self.cum.append(c)
            c += size
        self.total_missing = c

    def _ext(self, orig):
        """Map an original position to the extracted-stream position.
        Returns (ext_pos, in_gap:bool)."""
        # binary search: count gaps fully before orig
        lo, hi = 0, len(self.gaps)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.gaps[mid][0] <= orig:
                lo = mid + 1
            else:
                hi = mid
        k = lo  # first gap with pos > orig
        if k > 0:
            gpos, gsize = self.gaps[k - 1]
            if orig < gpos + gsize:
                return gpos - self.cum[k - 1], True  # inside gap k-1
        return orig - (self.cum[k] if k < len(self.cum) else self.total_missing), False

    def byte(self, orig):
        p, ingap = self._ext(orig)
        if ingap or p >= len(self.d) or p < 0:
            return 0
        return self.d[p]

    def bytes_at(self, orig, n):
        out = bytearray()
        for i in range(n):
            out.append(self.byte(orig + i))
        return bytes(out)

    def u16(self, orig):
        b = self.bytes_at(orig, 2)
        return b[0] | (b[1] << 8)

    def u32(self, orig):
        b = self.bytes_at(orig, 4)
        return b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)
