# -*- coding: utf-8 -*-

import argparse
import logging

from array import array
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.colors import LinearSegmentedColormap
from pylab import contour, contourf


from il2fb.maps.heightmaps.constants import HEIGHT_PACK_FORMAT
from il2fb.maps.heightmaps.constants import MAP_SCALE
from il2fb.maps.heightmaps.logging import setup_logging


LOG = logging.getLogger(__name__)

CMAP_DATA = (
    (0.27058823529411763, 0.45882352941176469 , 0.70588235294117652),
    (0.45490196078431372, 0.67843137254901964 , 0.81960784313725488),
    (0.6705882352941176 , 0.85098039215686272 , 0.9137254901960784 ),
    (0.8784313725490196 , 0.95294117647058818 , 0.97254901960784312),
    (1.0                , 1.0                 , 0.74901960784313726),
    (0.99607843137254903, 0.8784313725490196  , 0.56470588235294117),
    (0.99215686274509807, 0.68235294117647061 , 0.38039215686274508),
    (0.95686274509803926, 0.42745098039215684 , 0.2627450980392157 ),
    (0.84313725490196079, 0.18823529411764706 , 0.15294117647058825),
    (0.6470588235294118 , 0.0                 , 0.14901960784313725),
)
CMAP = LinearSegmentedColormap.from_list('il2fb-heights', CMAP_DATA, 256)


def load_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render heightmap of a given location of "
            "«IL-2 Sturmovik: Forgotten Battles»"
        ),
    )
    parser.add_argument(
        '--height',
        dest='height',
        type=int,
        required=True,
        help=f"Map height in meters. Must be proportional to {MAP_SCALE}",
    )
    parser.add_argument(
        '--width',
        dest='width',
        type=int,
        required=True,
        help=f"Map width in meters. Must be proportional to {MAP_SCALE}",
    )
    parser.add_argument(
        '-i', '--in',
        dest='input_file_path',
        type=lambda x: Path(x).resolve(),
        default="heightmap",
        help="Input file path. Default: 'heightmap'",
    )
    parser.add_argument(
        '-o', '--out',
        dest='output_file_path',
        type=lambda x: Path(x).resolve(),
        default="heightmap.png",
        help="Output file path. Default: 'heightmap.png'",
    )
    parser.add_argument(
        '--isostep',
        dest='isostep',
        type=int,
        default=200,
        help="Step in meters between isolines. Default: 400",
    )
    parser.add_argument(
        '-r', '--dpi',
        dest='dpi',
        type=int,
        default=48,
        help="Output resolution in DPI. Default: 48",
    )
    args = parser.parse_args()

    if args.height % MAP_SCALE != 0:
        parser.error(f"Map height must be proportional to {MAP_SCALE}")

    if args.width % MAP_SCALE != 0:
        parser.error(f"Map width must be proportional to {MAP_SCALE}")

    return args


def render(
    src: array,
    height: int,
    width: int,
    isostep: int,
    dpi: int,
    output_file_path: Path,
) -> None:

    height = height // MAP_SCALE
    width = width // MAP_SCALE

    data = np.array(src).reshape((height, width))
    image_size = (
        (width / dpi),
        (height / dpi)
    )
    isolevels = list(range(0, data.max(), isostep))

    plt.clf()
    plt.figure(dpi=300)
    fig = plt.figure(figsize=image_size, frameon=False)
    fig.add_axes([0, 0, 1, 1])

    contourf(data, 256, cmap=CMAP)
    contour(data, isolevels, colors='#303030', linewidths=0.2)

    plt.axis('off')
    plt.savefig(str(output_file_path), bbox_inches=0, dpi=dpi)


def main() -> None:
    setup_logging()

    args = load_args()
    src = array(HEIGHT_PACK_FORMAT)

    with args.input_file_path.open('rb') as f:
        src.frombytes(f.read())

    render(
        src=src,
        height=args.height,
        width=args.width,
        isostep=args.isostep,
        dpi=args.dpi,
        output_file_path=args.output_file_path,
    )


if __name__ == '__main__':
    main()
