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
    layer = Image.new('RGBA', im.size, (0, 0, 0, 0))

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

    fill_color = (255, 0, 0)
    clear_color = (0,)*4

    im = Image.open(tpath)
    idata = im.load()
    w, h = im.size
    mdata = []
    for _ in xrange(h):
        mdata.append([-1, ]*w)

    src = array('H')
    with open(spath, 'r') as f:
        src.fromstring(f.read())
    src = np.array(src).reshape((h, w))

    groups = []
    group_num = 0

    def not_water(x, y):
        r, g, b = idata[x, y]
        return False if b > r and b > g else True

    for i in xrange(h):
        for j in xrange(w):
            cg = mdata[i][j]
            if cg >= 0:
                continue
            ch = src[i, j]

            group = []
            if not_water(j, i):
                group.append((i, j))

            to_fill = []
            to_fill.append((i-1, j))
            to_fill.append((i+1, j))
            to_fill.append((i, j-1))
            to_fill.append((i, j+1))

            while to_fill:
                x, y = to_fill.pop(0)
                if x < 0 or x >= h or y < 0 or y >= w:
                    continue
                ag = mdata[x][y]
                if ag >= 0:
                    continue
                ah = src[x, y]
                if ch == ah:
                    mdata[x][y] = group_num
                    if not_water(y, x):
                        group.append((x, y))
                    to_fill.append((x-1, y))
                    to_fill.append((x+1, y))
                    to_fill.append((x, y-1))
                    to_fill.append((x, y+1))

            if group:
                groups.append(group)
                group_num += 1

    d = [clear_color, ]*h*w
    # for i in xrange(h):
    #         d[i*w + 3] = fill_color
    for g in groups:
        if len(g) < 50:
            continue
        for y, x in g:
            d[y*w+x] = fill_color

    mask = Image.new("RGBA", (w, h))
    mask.putdata(d)
    result = add_mask(im, mask, 0.4)
    result.save(ppath)


if __name__ == '__main__':
    main()
