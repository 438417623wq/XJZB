import sys, re, html
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
raw = open(r"F:\KF\XJZB\scr_research\wiki_doodad.html", encoding="utf-8", errors="replace").read()
raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
raw = re.sub(r"(?i)</(p|li|tr|div|h[1-6])>", "\n", raw)
txt = re.sub(r"(?s)<[^>]+>", "", raw)
txt = html.unescape(txt)
lines = [l.strip() for l in txt.splitlines()]
out = [l for l in lines if l]
open(r"F:\KF\XJZB\scr_research\wiki_doodad.txt", "w", encoding="utf-8").write("\n".join(out))
print("lines:", len(out))
for i, l in enumerate(out):
    print(f"{i+1}| {l[:220]}")
