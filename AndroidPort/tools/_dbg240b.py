import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''        boolean linked = admitted.get() != null && jr.get() != null && jr.get().ok();
        boolean lockstepHeld = false;
        boolean bothTouchedTeam0 = false;
'''
new = '''        boolean linked = admitted.get() != null && jr.get() != null && jr.get().ok();
        sb.append(" linked=").append(linked)
          .append(" host=").append(admitted.get() != null)
          .append(" joinErr=").append(jr.get() == null ? "null" : jr.get().error);
        boolean lockstepHeld = false;
        boolean bothTouchedTeam0 = false;
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("patched")