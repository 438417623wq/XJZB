import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm
todo = [("maps\\BroodWar\\WebMaps\\(4)Crossroads.scm", "crossroads", "十字路口"),
        ("maps\\(6)New Gettysburg.scm", "newgettysburg", "新葛底斯堡")]
ok = 0
for src, mid, name in todo:
    if pm.build_map(src, mid, name):
        ok += 1
print("built %d/%d" % (ok, len(todo)))
pm.write_map_index()
print("index written")
