"""Final HudPreview.java repair: the literals whose damaged tail also ate the
closing quote. Each is identified by line number and patched as a whole line,
so no escape-encoding guesswork is involved. Every line is asserted to still
contain the damage marker before it is touched.
"""
P = r'F:\KF\XJZB\AndroidPort\tools\HudPreview.java'

# line number -> (expected fragment, replacement line)
FIXES = {
    443: ('\ufffd', '                names = new String[]{"\u653b\u51fb", "\u505c\u6b62", "\u5de1\u903b",'),
    444: ('\ufffd', '                                     "\u4fee\u7406", "\u5efa\u9020", null, null, null, null};'),
    449: ('\ufffd', '                names = new String[]{"\u661f\u6e2f", "\u519b\u68b0\u5e93", "\u79d1\u5b66\u8bbe\u65bd",'),
    469: ('\ufffd', '            names = new String[]{"\u67a2\u7ebd", "\u6c34\u6676\u5854", "\u5438\u6536\u7ad9",'),
    470: ('\ufffd', '                                 "\u4f20\u9001\u95e8", "\u953b\u9020\u5382", "\u5149\u5b50\u70ae",'),
    489: ('\ufffd', '            names = new String[]{"\u653b\u51fb", "\u653b\u51fb\u79fb\u52a8", "\u505c\u6b62", "\u5de1\u903b",'),
    676: ('\ufffd', '        String[] labels = {"\u6682\u505c", "\u8d44\u6e90", "\u65f6\u95f4", "\u6218\u51b5", "\u5c0f\u5730\u56fe", "\u7f16\u961f", "\u4fe1\u606f", "\u4e5d\u5bab\u683c"};'),
    740: ('\ufffd', '        String[] stateName = {"\u7a7a\u9009", "\u5355\u9009", "\u5efa\u9020\u9875"};'),
}

lines = open(P, encoding='utf-8').read().split('\n')
for ln, (frag, new) in FIXES.items():
    old = lines[ln - 1]
    assert frag in old, 'line %d lost its damage marker: %r' % (ln, old)
    lines[ln - 1] = new

out = '\n'.join(lines)
open(P, 'w', encoding='utf-8', newline='').write(out)

print('U+FFFD left:', out.count('\ufffd'))
bad = [n for n, l in enumerate(out.split('\n'), 1) if '\ufffd' in l]
print('lines still damaged:', bad)
