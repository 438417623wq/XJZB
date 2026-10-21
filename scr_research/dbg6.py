import re, sys, html
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
t = open(r"F:\KF\XJZB\scr_research\bing1.html", encoding="utf-8", errors="replace").read()
# strip tags
txt = re.sub(r"<script.*?</script>", " ", t, flags=re.S|re.I)
txt = re.sub(r"<style.*?</style>", " ", txt, flags=re.S|re.I)
txt = re.sub(r"<[^>]+>", " ", txt)
txt = html.unescape(txt)
txt = re.sub(r"\s+", " ", txt)
for m in re.finditer(r"DDDATA", txt):
    print("...", txt[max(0,m.start()-300):m.start()+300].strip(), "\n")
print("--- total DDDATA mentions:", len(re.findall("DDDATA", txt)))
print("--- bing body sample:", txt[:600])
