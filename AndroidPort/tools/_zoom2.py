from PIL import Image
im = Image.open(r"out\hud_v242_widgets.png")
ox, oy = 12, 44
crop = im.crop((ox+640, oy+530, ox+1000, oy+720))
crop = crop.resize((crop.width*3, crop.height*3), Image.NEAREST)
crop.save(r"out\_zoom_info_queue_1280.png")
print("saved", crop.size)
