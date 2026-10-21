import urllib.request
u = "https://raw.githubusercontent.com/ShieldBattery/bw-chk/master/sprites.js"
try:
    d = urllib.request.urlopen(u, timeout=30).read()
    open("_sprites_js.txt","wb").write(d)
    print("ok", len(d))
except Exception as e:
    print("ERR", e)
