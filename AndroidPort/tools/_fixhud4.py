"""Last pass for HudPreview.java: the literals whose damaged tail ate the
closing characters too. Each one is unambiguous from the class constants and
from its own call site, so they are patched by exact context match.
"""
P = r'F:\KF\XJZB\AndroidPort\tools\HudPreview.java'

FIXES = [
    # SCV page 0: patrol / repair
    ('"\\u5de1\ufffd?,\n                                     "\\u4fee\\u7406"',
     '"\u5de1\u903b",\n                                     "\u4fee\u7406"'),
    # SCV page 0: build
    ('"\\u4fee\\u7406", "\\u5efa\ufffd?, null, null, null, null};',
     '"\u4fee\u7406", "\u5efa\u9020", null, null, null, null};'),
    # page 2: armory
    ('"\\u519b\\u68b0\ufffd?, "\\u79d1\\u5b66\\u8bbe\\u65bd"',
     '"\u519b\u68b0\u5e93", "\u79d1\u5b66\u8bbe\u65bd"'),
    # protoss page: pylon / assimilator / photon cannon
    ('"\\u6c34\\u6676\ufffd?, "\\u5438\\u6536\ufffd?,',
     '"\u6c34\u6676\u5854", "\u5438\u6536\u7ad9",'),
    ('"\\u953b\\u9020\\u5382", "\\u5149\\u5b50\ufffd?,',
     '"\u953b\u9020\u5382", "\u5149\u5b50\u70ae",'),
    # combat unit card: patrol
    ('"\\u505c\\u6b62", "\\u5de1\ufffd?,\n                                 null',
     '"\u505c\u6b62", "\u5de1\u903b",\n                                 null'),
    # ellipsis used by the name/queue truncation helpers
    ('nm = nm.substring(0, nm.length() - 2) + "\ufffd?;',
     'nm = nm.substring(0, nm.length() - 2) + "\u2026";'),
    ('qn = qn.substring(0, qn.length() - 2) + "\ufffd?;',
     'qn = qn.substring(0, qn.length() - 2) + "\u2026";'),
    # widget labels: minimap
    ('"\\u6218\\u51b5", "\\u5c0f\\u5730\ufffd?, "\\u7f16\\u961f"',
     '"\u6218\u51b5", "\u5c0f\u5730\u56fe", "\u7f16\u961f"'),
    ('"\\u4fe1\\u606f", "\\u4e5d\\u5bab\ufffd?};',
     '"\u4fe1\u606f", "\u4e5d\u5bab\u683c"};'),
    # selection-state names: empty / single
    ('"\\u7a7a\ufffd?, "\\u5355\ufffd?, "\\u5efa\\u9020\\u9875"',
     '"\u7a7a\u9009", "\u5355\u9009", "\u5efa\u9020\u9875"'),
]

src = open(P, encoding='utf-8').read()
for old, new in FIXES:
    n = src.count(old)
    if n != 1:
        print('SKIP (found %d):' % n, old.encode('unicode_escape').decode('ascii'))
        continue
    src = src.replace(old, new)

open(P, 'w', encoding='utf-8', newline='').write(src)
print('U+FFFD left:', src.count('\ufffd'))
for n, line in enumerate(src.split('\n'), 1):
    if '\ufffd' in line or '?' in line and any(ord(c) > 127 for c in line):
        print('  line', n, line.strip().encode('unicode_escape').decode('ascii'))
