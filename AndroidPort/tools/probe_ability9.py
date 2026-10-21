from PIL import Image
im = Image.open("out/cmdicons_ability.png")
print(im.size)
# top-right region: columns 9-13 of 16? Let's crop right half, rows 0-6
w,h = im.size
crop = im.crop((int(w*0.55), 0, w, int(h*0.55)))
crop = crop.resize((crop.width*2, crop.height*2), Image.LANCZOS)
crop.save("out/cmdicons_ability_zoom.png")
print(crop.size)
