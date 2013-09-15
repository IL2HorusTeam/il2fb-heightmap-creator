# -*- coding: utf-8 -*-

import optparse
import os

from array import array
import numpy as np

from PIL import Image, ImageEnhance


def parse_args():
    usage = """usage: %prog --dir=SRC"""
    parser = optparse.OptionParser(usage)

    help = "Path to the map directory."
    parser.add_option('--dir', help=help)

    options, args = parser.parse_args()

    if not options.dir:
        parser.error("Path to map directory is not specified.")

    return options.dir


def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


def add_mask(im, mark, opacity=1):
    """Adds a watermark to an image."""
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0,0,0,0))

    for y in range(0, im.size[1], mark.size[1]):
        for x in range(0, im.size[0], mark.size[0]):
            layer.paste(mark, (x, y))

    # composite the watermark with the layer
    return Image.composite(layer, im, layer).convert("RGB")


def main():
    map_dir = parse_args()
    spath = os.path.join(map_dir, 'heights')
    tpath = os.path.join(map_dir, 'topographical.png')
    ppath = os.path.join(map_dir, 'plains.png')

    im = Image.open(tpath)
    h, w = im.size
    mask = Image.new("RGB", (h, w), (255, )*3)
    data = mask.load()

    src = array('H')
    with open(spath, 'r') as f:
        src.fromstring(f.read())
    src = np.array(src).reshape((w, h))

    fill_color = (255, 0, 0)
    i = 1
    while i < w:
        j = 1
        while j < h:
            if src[i][j] == src[i][j-1] and src[i][j] == src[i-1][j]:
                data[j, i] = data[j-1,i] = data[j,i-1] = fill_color
            j += 1
        i += 1

    result = add_mask(im, mask, 0.4)
    result.save(ppath)


if __name__ == '__main__':
    main()
