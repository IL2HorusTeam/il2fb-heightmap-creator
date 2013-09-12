# -*- coding: utf-8 -*-

from PIL import Image
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

    return options.src, (options.height/MAP_SCALE, options.width/MAP_SCALE)


class Renderer(object):

    def render(self, src):
        raise NotImplementedError

    @property
    def slug(self):
        raise NotImplementedError


class BlackAndWhiteRenderer(Renderer):

    slug = "bw"

    def render(self, src):

        def scale(elem):
            value = int(255*(elem/vmax))
            return (value, )*3

        vmax = float(max(src))
        return map(scale, src)


class JetGradientRenderer(Renderer):

    slug = "jet"

    def render(self, src):

        def get_color(v):
            v = v/emax
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
        emax = float(max(src))
        dv = vmax - vmin;
        return map(get_color, src)


class TerraRenderer(Renderer):

    slug = "terra"

    def __init__(self):
        self.tints = [
            (100, (31, 156, 126)),
            (200, (126, 156, 32)),
            (300, (238, 215, 83)),
            (450, (242, 201, 83)),
            (650, (245, 187, 80)),
            (900, (226, 166, 70)),
            (1100, (210, 146, 59)),
            (1300, (196, 129, 48)),
            (1500, (184, 112, 38)),
            (1700, (180, 111, 33)),
            (2000, (180, 104, 28)),
            (2300, (175, 90, 23)),
            (2600, (171, 86, 19)),
            (2900, (166, 83, 15)),
            (3200, (160, 79, 13)),
            (3500, (156, 75, 10)),
            (3800, (151, 71, 8)),
            (4100, (151, 71, 0)),
        ]

    def render(self, src):

        def get_color(v):
            for limit, color in self.tints:
                if v < limit:
                    return color
            return self.tints[-1][1]

        return map(get_color, src)


def main():
    spath, dimentions = parse_args()
    src = array('H')
    with open(spath, 'r') as f:
        src.fromstring(f.read())
    renders = [
        BlackAndWhiteRenderer(), JetGradientRenderer(), TerraRenderer(), ]
    for r in renders:
        im = Image.new('RGB', dimentions)
        im.putdata(r.render(src))
        im.show()
        dpath = "{:}.{:}.png".format(spath, r.slug)
        im.save(dpath)


if __name__ == '__main__':
    main()
