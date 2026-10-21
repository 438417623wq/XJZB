import re, sys, html
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\scr_research\staredit_chk.html"
t = open(p, encoding="utf-8", errors="replace").read()
# strip tags but keep line structure
t = re.sub(r"<script.*?</script>", "", t, flags=re.S|re.I)
t = re.sub(r"<style.*?</style>", "", t, flags=re.S|re.I)
t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
t = re.sub(r"</(p|li|tr|div|h1|h2|h3|h4|pre)>", "\n", t, flags=re.I)
t = re.sub(r"<[^>]+>", "", t)
t = html.unescape(t)
t = re.sub(r"[ \t]+", " ", t)
t = re.sub(r"\n{3,}", "\n\n", t)
open(r"F:\KF\XJZB\scr_research\staredit_chk.txt","w",encoding="utf-8").write(t)
lines = t.split("\n")
print("total lines:", len(lines))
for i,l in enumerate(lines):
    if re.search(r"DD2|DDATA|1\.18|doodad", l, re.I):
        print(i, "|", l.strip()[:400])
