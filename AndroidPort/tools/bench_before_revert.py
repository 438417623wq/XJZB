"""v2.43 section 2: back the v2.43 optimisations out of a copy of core/Game.java.

The plan's step-0 baseline wants a before/after frame-time table. The "after"
half is the shipped v2.43 build. The "before" half has to be an actual
measurement, not an estimate, so this script rewrites a *copy* of Game.java
(tools/bench_before_src) into its v2.42 shape and the bench is run against that
copy. Nothing under app/app/src is touched.

Four edits, one per v2.43 batch. Each is a literal string replacement so that a
source change makes this script fail loudly instead of silently measuring
something else.
"""

import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()

EDITS = [
    # ---- P0-a: undo the aura/detector count short-circuits ----------------
    (
        """        ensureAuraCounts();
        int team = e.team == 1 ? 1 : 0;
        statAuraQueries++;
        if (arbCount[team] == 0) return false;
        statAuraScans++;
        for (int i = 0, n = arbListN; i < n; i++) {
            Ent a = arbList[i];""",
        """        int team = e.team == 1 ? 1 : 0;
        statAuraQueries++;
        statAuraScans++;
        for (int i = 0, n = ents.size(); i < n; i++) {
            Ent a = ents.get(i);
            if (!"arbiter".equals(a.type.key)) continue;""",
    ),
    (
        """        ensureAuraCounts();
        int team = byTeam == 1 ? 1 : 0;
        statAuraQueries++;
        if (detCount[team] == 0) return false;
        statAuraScans++;
        for (int i = 0, n = detListN; i < n; i++) {
            Ent d = detList[i];""",
        """        int team = byTeam == 1 ? 1 : 0;
        statAuraQueries++;
        statAuraScans++;
        for (int i = 0, n = ents.size(); i < n; i++) {
            Ent d = ents.get(i);
            if (!d.type.detector) continue;""",
    ),
    # ---- P0-a: undo the idle-acquire phase stagger ------------------------
    (
        """            if (ents.size() < ACQUIRE_STAGGER_MIN
                    || (curRosterIdx & (ACQUIRE_PHASES - 1)) == (tick & (ACQUIRE_PHASES - 1))) {""",
        """            if (true) {""",
    ),
    # ---- P0-b: undo the spatial grid (every query walks the roster) -------
    (
        """    private int gatherNear(float x, float y, float reach) {
        ensureSpatial();
        statGridQueries++;
        qScratchN = 0;""",
        """    private int gatherNear(float x, float y, float reach) {
        statGridQueries++;
        qScratchN = 0;
        if (true) {
            int n = ents.size();
            ensureScratch(n);
            for (int i = 0; i < n; i++) qScratch[qScratchN++] = i;
            statGridCandidates += qScratchN;
            return qScratchN;
        }
        ensureSpatial();""",
    ),
    # ---- P0-c: undo the path budget (serve the whole queue every tick) ----
    (
        """        int served = 0;
        while (pathQueueHead < pathQueue.size() && served < PATH_BUDGET) {""",
        """        int served = 0;
        while (pathQueueHead < pathQueue.size()) {""",
    ),
]

for i, (old, new) in enumerate(EDITS):
    if src.count(old) != 1:
        print("REVERT-FAIL edit %d matched %d times" % (i, src.count(old)))
        sys.exit(1)
    src = src.replace(old, new)

open(path, "w", encoding="utf-8", newline="\n").write(src)
print("reverted %d edits in %s" % (len(EDITS), path))
