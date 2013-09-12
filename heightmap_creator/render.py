# -*- coding: utf-8 -*-

from PIL import Image, ImageFilter
import optparse

from array import array

from constants import MAP_SCALE


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


class Renderer(object):

    def render(self, src, dimentions):
        raise NotImplementedError

    @property
    def slug(self):
        raise NotImplementedError


class BlackAndWhiteRenderer(Renderer):

    slug = "bw"

    def render(self, src, dimentions):

        def get_color(v):
            value = int(255*(v/vmax))
            return (value, )*3

        vmax = float(max(src))

        im = Image.new('RGB', dimentions)
        im.putdata(map(get_color, src))
        return im


class JetGradientRenderer(Renderer):

    slug = "jet"

    def render(self, src, dimentions):

        def get_color(v):
            v = v/_max
            r, g, b = (1.0, 1.0, 1.0)
            if v < vmin:
                v = vmin
            if v > vmax:
                v = vmax
            if v < vmin + 0.25 * dv:
                r = 0;
                g = 4 * (v - vmin) / dv;
            elif v < vmin + 0.5 * dv:
                r = 0;
                b = 1 + 4 * (vmin + 0.25 * dv - v) / dv;
            elif v < vmin + 0.75 * dv:
                r = 4 * (v - vmin - 0.5 * dv) / dv;
                b = 0;
            else:
                g = 1 + 4 * (vmin + 0.75 * dv - v) / dv;
                b = 0;
            return (int(r*255), int(g*255), int(b*255))

        vmin = 0.0
        vmax = 1.0
        _max = float(max(src))
        dv = vmax - vmin;

        im = Image.new('RGB', dimentions)
        im.putdata(map(get_color, src))
        return im


class TerraRenderer(Renderer):

    slug = "terra"

    def __init__(self):
        self.tints = [
            '3b8513', '7e9c20', 'ead94b', 'f2c953', 'eebe5c', 'f5bb50',
            'd2923b', 'c48130', 'c18433', 'b87026', 'b46f21', 'b4681c',
            'af5a17', 'ab5613', 'a6530f', 'a04f0d', '9c4b0a', '974708',
            '974700', ]

    def render(self, src, dimentions):
        import struct

        _max = max(src)
        step = int(float(_max-50)/(len(self.tints)-1))
        colors = zip(range(50, _max, step), self.tints)

        def color(v):
            return struct.unpack('BBB', v.decode('hex'))

        def get_color(v):
            for limit, c in colors:
                if v < limit:
                    return color(c)
            return color(colors[-1][1])

        im = Image.new('RGB', dimentions)
        im.putdata(map(get_color, src))
        return im.filter(ImageFilter.DETAIL)


def render(src, dst_path, dimentions):
    h, w = dimentions
    h /= MAP_SCALE
    w /= MAP_SCALE
    renders = [
        BlackAndWhiteRenderer(), JetGradientRenderer(), TerraRenderer(), ]
    for r in renders:
        im = r.render(src, (w, h))
        dpath = "{:}.{:}.png".format(dst_path, r.slug)
        im.save(dpath)


def main():
    spath, dimentions = parse_args()
    src = array('H')
    with open(spath, 'r') as f:
        src.fromstring(f.read())
    render(src, spath, dimentions)


if __name__ == '__main__':
    main()
