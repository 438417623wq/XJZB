# _e23_revert.py -- undo the temporary m01 portrait fixture from _e23.py.
# Restores the pristine mission so the shipped build is unchanged.
import os, shutil

A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\missions\m01.json"
BAK = r"F:\KF\XJZB\AndroidPort\tools\out\m01.json.bak"

if not os.path.exists(BAK):
    print("NO BACKUP at", BAK, "-- nothing reverted")
    raise SystemExit(1)

shutil.copy2(BAK, A)
print("reverted", A, "from", BAK)
print("size now", os.path.getsize(A))
