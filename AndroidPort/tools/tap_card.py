"""Tap a command-card cell by (row, col) on the emulator.

GameView lays the 3x3 card out from the *view* height, which on this
emulator is the screen height minus the 75 px gesture-navigation inset
(the screenshot still includes that black strip, so using the raw image
height puts every tap one row too low).

Geometry, mirroring GameView.cardCell()/consoleH()/drawCmdCard():

    uiScale = density > 1.5 ? 2 : 1        (480 dpi -> 2)
    cs      = CELL_DP * uiScale            (100 px)
    gap     = CARD_GAP_DP * uiScale        (8 px)
    gridW   = gridH = 3*cs + 2*gap         (316 px)
    gx      = W - 12*uiScale - gridW
    bottomH = clamp(3*cs + 2*gap + CARD_PAD_DP*uiScale, 150*uiScale, viewH/2)
    gy      = viewH - bottomH + (bottomH - gridH)/2

Verified against three independently confirmed taps at 2992x1344:
  建造 (terran worker, row1 col2) -> (2918, 1101)
  更多 (terran build page 1, row2 col2) -> (2918, 1209)
  返回 (terran build page 2, row1 col0) -> (2702, 1101)

Usage:
    python tap_card.py <screenshot.png> <row> <col>            # print only
    python tap_card.py <screenshot.png> <row> <col> --tap      # tap too
"""
import subprocess
import sys

from PIL import Image

ADB = r"C:\Users\XiaoXin\AppData\Local\Android\Sdk\platform-tools\adb.exe"

CELL_DP = 50.0
CARD_GAP_DP = 4.0
CARD_PAD_DP = 10.0
UI_SCALE = 2
# gesture-navigation inset the view does not cover (75 px at density 480)
NAV_INSET = 75


def geometry(path, nav_inset=NAV_INSET):
    im = Image.open(path)
    W, H = im.size
    viewH = H - nav_inset
    ui = UI_SCALE
    cs = CELL_DP * ui
    gap = CARD_GAP_DP * ui
    budget = viewH * 0.50 - CARD_PAD_DP * ui - 2 * gap
    fit = budget / 3
    if fit < cs:
        cs = max(46.0 * ui, fit)
    grid = 3 * cs + 2 * gap
    gx = W - 12 * ui - grid
    bottomH = min(max(150.0 * ui, grid + CARD_PAD_DP * ui), viewH * 0.50)
    gy = viewH - bottomH + (bottomH - grid) / 2.0
    gy = min(gy, viewH - grid - 2 * ui)
    return W, H, cs, gap, gx, gy


def main():
    path = sys.argv[1]
    row, col = int(sys.argv[2]), int(sys.argv[3])
    W, H, cs, gap, gx, gy = geometry(path)
    x = gx + col * (cs + gap) + cs / 2
    y = gy + row * (cs + gap) + cs / 2
    print(f"image {W}x{H}  cell {cs:.0f} gap {gap:.0f}  origin ({gx:.0f},{gy:.0f})")
    print(f"row {row} col {col} -> ({x:.0f}, {y:.0f})")
    if "--tap" in sys.argv:
        subprocess.run([ADB, "shell", f"input tap {int(x)} {int(y)}"], check=False)
        print("tapped")


if __name__ == "__main__":
    main()
