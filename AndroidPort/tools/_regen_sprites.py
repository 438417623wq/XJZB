"""Regenerate the sprite pipeline into a temp dir, so the shipped tree can be
diffed against a fresh decode before anything is overwritten."""
import os, sys, shutil
import pipeline_sprites as P

TMP = r"F:\KF\XJZB\AndroidPort\tools\out\_regen"
if os.path.isdir(TMP):
    shutil.rmtree(TMP)
os.makedirs(TMP)
P.SPR = TMP
P.main()
print("regen into", TMP)
