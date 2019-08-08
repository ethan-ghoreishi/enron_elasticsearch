from PIL import Image

images = []
for i in imgs:
    images.append(i)

# images = map(Image.open, ['image-1.png', 'image-3.png', 'image-2.png'])
images = map(Image.open, images)
widths, heights = zip(*(i.size for i in images))

total_width = sum(widths)
max_height = max(heights)

new_im = Image.new('RGB', (total_width+30, max_height), color=0)

# images = map(Image.open, ['image-2.png','image-3.png', 'image-1.png'])
images = map(Image.open, images)
x_offset = 0
for im in images:
    new_im.paste(im, (x_offset,0))
    x_offset += im.size[0]+10

new_im.save('test.png')