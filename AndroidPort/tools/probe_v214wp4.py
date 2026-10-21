from PIL import Image
import os
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\wp4"
os.makedirs(TMP, exist_ok=True)
pl = Image.open(os.path.join(SPR,"plasma_b.webp")).convert("RGBA")
emp = Image.open(os.path.join(SPR,"emp_b.webp")).convert("RGBA")
print("plasma", pl.size, "emp", emp.size)
# F: SAME canvas 2048x768 but filled with a DIFFERENT image (emp tiled) -> dimension vs content
tile = Image.new("RGBA",(2048,768),(0,0,0,0))
for j in range(0,768,252):
    for i in range(0,2048,1764):
        tile.alpha_composite(emp,(i,j))
tile.save(os.path.join(TMP,"F_emp_2048x768.webp"),"WEBP",lossless=True,method=6)
# G: plasma content, canvas 2048x768 but alpha zeroed (all transparent)
blank = Image.new("RGBA",(2048,768),(0,0,0,0))
blank.save(os.path.join(TMP,"G_blank_2048x768.webp"),"WEBP",lossless=True,method=6)
# H: plasma content kept, canvas 2048x768, but RGB forced to a flat colour (alpha only)
flat = pl.copy(); flat.paste((255,0,0,0),(0,0,2048,768), Image.new("L",(2048,768),0))
fa = pl.getchannel("A")
flat = Image.merge("RGBA",(Image.new("L",(2048,768),255),Image.new("L",(2048,768),0),Image.new("L",(2048,768),0),fa))
flat.save(os.path.join(TMP,"H_alphaonly_2048x768.webp"),"WEBP",lossless=True,method=6)
# I: plasma, non-pow2 canvas 2016x768
pl.crop((0,0,2016,768)).save(os.path.join(TMP,"I_2016x768.webp"),"WEBP",lossless=True,method=6)
# J: plasma, 2048x512
pl.crop((0,0,2048,512)).save(os.path.join(TMP,"J_2048x512.webp"),"WEBP",lossless=True,method=6)
# K: plasma resized to 1024x768
pl.resize((1024,768),Image.NEAREST).save(os.path.join(TMP,"K_1024x768.webp"),"WEBP",lossless=True,method=6)
for f in sorted(os.listdir(TMP)):
    print("  %-32s %d bytes" % (f, os.path.getsize(os.path.join(TMP,f))))
