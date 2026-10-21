import os
base = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
old  = r"F:\KF\XJZB\AndroidPort\tools\out\_v241_webp"
pairs = [("crusader/c_0_0.webp","crusader__c_0_0.webp"),
         ("crusader/c_11_7.webp","crusader__c_11_7.webp"),
         ("divide/c_0_0.webp","divide__c_0_0.webp")]
for new, o in pairs:
    a = open(os.path.join(base,new),"rb").read(20)
    b = open(os.path.join(old,o),"rb").read(20)
    print(new)
    print("   new:", a.hex(" "))
    print("   old:", b.hex(" "))
