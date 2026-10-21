"""v2.42 defect-B geometry simulator.

Reproduces GameView.render()'s chunk-dst computation exactly and reports any
screen scanline that no chunk's dst covers. If this finds a gap, the black bar
is pure geometry; if it does not, the gap must come from runtime state.
"""
import math

CS = 512
BLEED = 4


def floor(v):
    return int(math.floor(v))


def trunc(v):
    return int(v)          # Java (int) cast == truncation toward zero


def scan(W, H, zoom, camX, camY, wPx, hPx):
    centerY = H / 2.0
    centerX = W / 2.0

    def sx(wx):
        return (wx - camX) * zoom + centerX

    def sy(wy):
        return (wy - camY) * zoom + centerY

    def wx(x):
        return (x - centerX) / zoom + camX

    def wy(y):
        return (y - centerY) / zoom + camY

    cx0 = max(0, trunc(wx(0) / CS))
    cx1 = min((wPx - 1) // CS, trunc(wx(W) / CS))
    cy0 = max(0, trunc(wy(0) / CS))
    cy1 = min((hPx - 1) // CS, trunc(wy(H) / CS))

    rowcov = [0] * (H + 2)
    colcov = [0] * (W + 2)
    for cy in range(cy0, cy1 + 1):
        dy0 = floor(sy(cy * CS))
        dy1 = floor(sy(min(cy * CS + CS, hPx))) + BLEED
        if dy1 > dy0:
            for y in range(max(0, dy0), min(H, dy1)):
                rowcov[y] += 1
    for cx in range(cx0, cx1 + 1):
        dx0 = floor(sx(cx * CS))
        dx1 = floor(sx(min(cx * CS + CS, wPx))) + BLEED
        if dx1 > dx0:
            for x in range(max(0, dx0), min(W, dx1)):
                colcov[x] += 1

    rows = [y for y in range(H) if rowcov[y] == 0]
    cols = [x for x in range(W) if colcov[x] == 0]
    return rows, cols, (cx0, cx1, cy0, cy1)


def runs(v):
    if not v:
        return []
    out, s, p = [], v[0], v[0]
    for i in v[1:]:
        if i != p + 1:
            out.append((s, p, p - s + 1))
            s = i
        p = i
    out.append((s, p, p - s + 1))
    return out


if __name__ == "__main__":
    print("== divide 2048x2048, screen 2608x1200, zoom 1.56 ==")
    W, H, zoom, wPx, hPx = 2608, 1200, 1.56, 2048, 2048
    halfW = W / 2.0 / zoom
    halfTop = (H / 2.0) / zoom
    halfBot = (H - H / 2.0) / zoom
    loY, hiY = halfTop, max(halfTop, hPx - halfBot)
    loX, hiX = halfW, max(halfW, wPx - halfW)
    print("  camX in [%.1f, %.1f]  camY in [%.1f, %.1f]" % (loX, hiX, loY, hiY))

    bad = 0
    worst = None
    for i in range(0, 201):
        for j in range(0, 201):
            camX = loX + (hiX - loX) * i / 200.0
            camY = loY + (hiY - loY) * j / 200.0
            rows, cols, rng = scan(W, H, zoom, camX, camY, wPx, hPx)
            if rows or cols:
                bad += 1
                if worst is None or len(rows) > len(worst[2]):
                    worst = (camX, camY, rows, cols, rng)
    print("  camera grid 201x201: %d positions leave a gap" % bad)
    if worst:
        camX, camY, rows, cols, rng = worst
        print("  worst cam=(%.2f,%.2f) ranges=%s" % (camX, camY, rng))
        print("    uncovered rows:", runs(rows))
        print("    uncovered cols:", runs(cols))

    print()
    print("== also scan zoom values on the same map ==")
    for zoom in (0.5, 0.75, 1.0, 1.25, 1.56, 2.0, 2.5, 3.0):
        halfW = W / 2.0 / zoom
        halfTop = (H / 2.0) / zoom
        halfBot = (H - H / 2.0) / zoom
        loY, hiY = halfTop, max(halfTop, hPx - halfBot)
        loX, hiX = halfW, max(halfW, wPx - halfW)
        n = 0
        worst = None
        for i in range(0, 41):
            for j in range(0, 41):
                camX = loX + (hiX - loX) * i / 40.0
                camY = loY + (hiY - loY) * j / 40.0
                rows, cols, rng = scan(W, H, zoom, camX, camY, wPx, hPx)
                if rows or cols:
                    n += 1
                    if worst is None or len(rows) > len(worst[2]):
                        worst = (camX, camY, rows, cols, rng)
        print("  zoom=%.2f gap positions=%4d" % (zoom, n), end="")
        if worst:
            print("  worst cam=(%.1f,%.1f) rows=%s cols=%s"
                  % (worst[0], worst[1], runs(worst[2]), runs(worst[3])))
        else:
            print()
