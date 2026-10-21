import io
txt = (
"# v2.20 batch 5: the shipped replays. name|map|title\n"
"# Each file is a real recording (tools/ReplayGen.java) whose determinism\n"
"# was verified before it landed: the recorded stream replayed into a fresh\n"
"# Game matches the live match's stateHash at every second.\n"
"bloodbath_demo|bloodbath|\u8840\u6d74 \u00b7 \u4eba\u65cf\u5f00\u5c40\u6f14\u793a\n"
"losttemple_demo|losttemple|\u5931\u843d\u795e\u6bbf \u00b7 \u866b\u65cf\u5f00\u5c40\u6f14\u793a\n"
"river_demo|river|\u6cb3\u6d41 \u00b7 \u661f\u7075\u5f00\u5c40\u6f14\u793a\n"
)
io.open("app/app/src/main/assets/replays/index.txt","w",encoding="utf-8",newline="\n").write(txt)
print("index written")
