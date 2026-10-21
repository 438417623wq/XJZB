p="pipeline_maps.py"
s=open(p,encoding="utf8").read()

old_maps = '''MAPS = [
    ("maps\\\\(4)Blood Bath.scm", "bloodbath", "血浴"),
    ("maps\\\\(2)Bottleneck.scm", "bottleneck", "瓶颈"),
    ("maps\\\\(2)Boxer.scm", "boxer", "拳王"),
    ("maps\\\\(8)The Hunters.scm", "hunters", "猎手"),
    ("maps\\\\(4)Dark Crystal.scm", "darkcrystal", "暗黑水晶"),
    ("maps\\\\(2)River Crossing.scm", "river", "渡河"),
    ("maps\\\\(3)Three Kingdoms.scm", "3kingdoms", "三国"),
    ("maps\\\\(2)The Small Divide.scm", "divide", "小分界"),
    ("maps\\\\(4)Cyclone.scm", "cyclone", "风暴"),
    ("maps\\\\(2)Volcanis.scm", "volcanis", "火山"),
]
'''
print("old_maps found:", old_maps in s)
