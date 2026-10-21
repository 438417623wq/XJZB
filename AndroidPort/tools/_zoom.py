from PIL import Image
im = Image.open(r"out\hud_v242_widgets.png")
# left tile origin (12,44), tile 1280x720, uiScale=2
ox, oy = 12, 44
# info panel 676..820 x 560..704 ; groups 348..656 x 576..704
crop = im.crop((ox+330, oy+540, ox+860, oy+720))
crop = crop.resize((crop.width*2, crop.height*2), Image.NEAREST)
crop.save(r"out\_zoom_groups_info_1280.png")
print("saved", crop.size)
