# -*- coding: utf-8 -*-

import optparse

from array import array
from matplotlib.cm import get_cmap
from matplotlib.colors import Normalize

import matplotlib.pyplot as plt
import numpy as np

from PIL import Image, ImageFilter
from pylab import contour, contourf, savefig, cm, clabel, figure

from constants import MAP_SCALE, MAX_HEIGHT


def parse_args():
    usage = """usage: %prog --src=SRC --height=HEIGHT --width=WIDTH"""
    parser = optparse.OptionParser(usage)

    help = "Path to the source heightmap binary data file."
    parser.add_option('--src', help=help)

    help = "Map height in meters."
    parser.add_option('--height', type='int', help=help)

    help = "Map width in meters."
    parser.add_option('--width', type='int', help=help)

    options, args = parser.parse_args()

    if not options.src:
        parser.error("Path to source binary data file is not specified.")

    if not options.height:
        parser.error("Map height is not specified.")
    if options.height % MAP_SCALE != 0:
        parser.error("Map height is not proportional to %s." % MAP_SCALE)

    if not options.width:
        parser.error("Map width is not specified.")
    if options.width % MAP_SCALE != 0:
        parser.error("Map width is not proportional to %s." % MAP_SCALE)

    return options.src, (options.height, options.width)


def render(src, dst_path, dimentions, isostep=400, dpi=48):
    h, w = dimentions
    h /= MAP_SCALE
    w /= MAP_SCALE
    cmap_names = [
        ('RdYlGn_r', 'terrain'),
        ('jet', 'jet'),
    ]
    data = np.array(src).reshape((h, w))[::-1]
    size = (float(h)/dpi, float(w)/dpi)
    isolevels = [_ for _ in range(0, MAX_HEIGHT, isostep)]

    for cmap_name, slug in cmap_names:
        plt.clf()
        fig = plt.figure(figsize=size, frameon=False)
        fig.add_axes([0, 0, 1, 1])

        contourf(data, 256, cmap=get_cmap(cmap_name))
        C = contour(data, isolevels, colors='black', linewidth=.2)
        clabel(C, inline=True, fontsize=11)
        plt.axis('off')
        dpath = "{:}.{:}.png".format(dst_path, slug)
        plt.savefig(dpath, bbox_inches=0, dpi=dpi)
        print "'{:}' saved.".format(slug)


def main():
    spath, dimentions = parse_args()
    src = array('H')
    with open(spath, 'r') as f:
        src.fromstring(f.read())
    render(src, spath, dimentions)


if __name__ == '__main__':
    main()
