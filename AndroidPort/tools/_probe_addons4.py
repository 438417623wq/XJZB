import sc_archive, grp as grpm
from PIL import Image
ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
wpe, _ = SD.read_with_gaps(r"tileset\jungle.wpe")
PAL = [(wpe[i*4], wpe[i*4+1], wpe[i*4+2]) for i in range(256)]
names = ["control.grp", "controlT.grp", "machines.grp", "physics.grp", "ComSat.grp",
         "comsat.grp", "nukesilo.grp", "nukemiss.grp"]
tiles = []
for nm in names:
    p = "unit\\terran\\" + nm
    try:
        data, gaps = SD.read_with_gaps(p)
        fr, mw, mh = grpm.decode_grp(data, gaps)
        print(nm, "frames=%d max=%dx%d f0=%dx%d" % (len(fr), mw, mh, fr[0]["w"], fr[0]["h"]))
        f = fr[0]
        im = Image.new("RGBA", (f["w"], f["h"]), (0,0,0,0))
        px = im.load()
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y*f["w"]+x]
                if v == 255: continue
                px[x,y] = PAL[v] + (255,)
        tiles.append((nm, im))
    except Exception as e:
        print(nm, "ERR", type(e).__name__, e)
if tiles:
    W = sum(t[1].width for t in tiles) + 10*len(tiles)
    H = max(t[1].height for t in tiles) + 10
    sheet = Image.new("RGB", (W, H), (40,40,40))
    x = 5
    for nm, im in tiles:
        sheet.paste(im, (x, 5), im)
        x += im.width + 10
    sheet = sheet.resize((W*3, H*3), Image.NEAREST)
    sheet.save(r"F:\KF\XJZB\AndroidPort\tools\out\_addons_sheet.png")
    print("saved", sheet.size, "order:", [t[0] for t in tiles])
SD.close()
