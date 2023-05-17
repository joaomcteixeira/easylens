#!/usr/bin/python
"""
General script to read lif files from Leica microscopes and treat its images.

By Joao MC Teixeira.
"""
import argparse
import os
from pathlib import Path

import numpy as np
from PIL import Image
from matplotlib import pyplot as plt, cm
from matplotlib.colors import LinearSegmentedColormap
from readlif.reader import LifFile
from readlif.utilities import get_xml


cmap_bf       =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "white"])
cmap_cyan     =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "cyan"])
cmap_dapi     =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "blue"])
cmap_green    =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "lime"])
cmap_magenta  =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "magenta"])
cmap_orange   =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "orange"])
cmap_red      =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "red"])
cmap_yellow   =  LinearSegmentedColormap.from_list("mycmap",  ["black",  "yellow"])

LUT = {
    'bf': cmap_bf,  # bright field
    'dapi': cmap_dapi,
    'red': cmap_red,
    'cyan': cmap_cyan,
    'green': cmap_green,
    'magenta': cmap_magenta,
    'orange': cmap_orange,
    'yellow': cmap_yellow,
    'blue': cmap_dapi,
    }


ap = argparse.ArgumentParser()

ap.add_argument(
    '-p',
    '--lif',
    help='Path to .lif project',
    type=Path,
    required=True,
    )

ap.add_argument(
    '-i',
    '--indexes',
    help='Image index of the project.',
    type=int,
    default=None,
    nargs='+',
    )

ap.add_argument(
    '-c',
    '--channels',
    help='Channels to display',
    type=int,
    default=None,
    nargs='+',
    )

ap.add_argument(
    '-z',
    '--zindex',
    help='Z index to display',
    type=int,
    default=0,
    )

ap.add_argument(
    '-l',
    '--lut',
    dest='cmaps',
    help='Look Up Table',
    choices=list(LUT.keys()),
    nargs='+',
    )

ap.add_argument(
    '-lt',
    '--low-threshold',
    help=(
        'Lower intensity threshold. Pixels with intensity lower or equal than '
        'this value will be shown black. Accepts any value.'
        ),
    default=0,
    )

ap.add_argument(
    '-ht',
    '--high-threshold',
    help=(
        'High intensity threshold. Pixels with intensity higher or equal than '
        'this value will be shown of respective cmap color. Accepts any value.'
        ),
    default=4095,
    )

ap.add_argument(
    '-o',
    '--output',
    help=(
        'Path to the output image. '
        'If `None` is given, the name of the project is taken as prefix. '
        'If a folder is given, save images in the folder. '
        'Else, uses input string as prefix, saves in current working directory.'
        ),
    type=str,
    default=None,
    nargs='?',
    )


def maincli():
    cmd = ap.parse_args()
    main(**vars(cmd))
    return


def main(
        lif,
        indexes=None,
        channels=None,
        zindex=0,
        cmaps=None,
        low_threshold=0,
        high_threshold=4095,
        output=None,
        ):

    project = LifFile(lif)

    if output is None:
        output_prefix = Path(lif).stem
        output_fmt = output_prefix + "_i{}_z{}_c{}"
    elif Path(output).is_dir():
        output_fmt = os.fspath(Path(output, "i{}_z{}_c{}"))  # convert to str
    else:
        output_fmt = output + "_i{}_z{}_c{}"

    indexes = range(project.num_images) if indexes is None else indexes
    for i in indexes:
        img = project.get_image(i)

        pix_arrays = []
        channels = range(img.channels) if channels is None else channels
        for channel in channels:
            try:
                img_channel = img.get_frame(z=zindex, t=0, c=channel)
            except ValueError:
                # channel number does not exist.
                # readlif lib fails to correctly identify the number of channels
                break
            else:
                pix_arrays.append(np.array(img_channel))

        try:
            fig_size = (
                pix_arrays[0].shape[1] / 1000,
                pix_arrays[0].shape[0] / 1000,
                )
        except IndexError:
            print(f'> warning: channels {channel} does not exist for index {i} - skiping')
            continue

        plt.figure(figsize=fig_size, dpi=100)

        black_background = np.full(pix_arrays[0].shape, 1)
        plt.imshow(black_background, vmin=0, vmax=1, cmap=cmap_bf)

        cmaps = list(LUT.keys()) if cmaps is None else cmaps
        alpha = 0.5 if len(pix_arrays) > 1 else 1
        for cmap, pix_array in zip(cmaps, pix_arrays):
            plt.imshow(
                pix_array,
                cmap=LUT[cmap],
                vmin=low_threshold,
                vmax=high_threshold,
                alpha=alpha,
                )

        plt.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        _fname = output_fmt.format(i, zindex, '-'.join(map(str, channels)))
        fname = Path(_fname).with_suffix('.png')
        plt.savefig(fname, dpi=1000, transparent=True)
        print(f'> saved: {os.fspath(fname)}')

        plt.close()
        del img

    return


if __name__ == "__main__":
    maincli()
