#!/usr/bin/env python3
# lid: lo-fi image dithering
# written by sloum, khoroo
# licence: public domain - use it, improve it, share it!
#########

import argparse
import os
import os.path
from pathlib import Path
from random import randint
from typing import Generator, Optional
import itertools
from PIL import Image
from tqdm import tqdm


def iter_square(x: int, y: int, size: int) -> Generator[tuple[int, int], None, None]:
    for dx in range(size):
        for dy in range(size):
            yield x + dx, y + dy


def colorize(image: Image) -> Image:
    (width, height) = image.size
    ratio = 2
    ret = Image.new("RGB", (width * ratio, height * ratio))
    xy_generator = ((x, y) for x in range(width) for y in range(height))
    image_data = list(image.getdata())
    it_colors = itertools.cycle(((255, 0, 0), (0, 255, 0), (0, 0, 255)))

    data = [
        next(it_colors) if pixel == 1 else (255, 255, 255)
        for xy, pixel in zip(xy_generator, image_data)
        for _ in iter_square(*xy, ratio)
    ]

    ret.putdata(data, scale=1.0, offset=0.0)

    return ret


def save_image(image: Image, path: Path, quality: int) -> None:
    image.save(str(path), optimize=True, quality=quality)


def new_image(width: int, height: int) -> Image:
    return Image.new("1", (width, height))


def ordered_dither_4(image: Image) -> Image:
    width, height = image.size
    new = new_image(*image.size)
    new_pixels = new.load()
    dots = [[64, 128], [192, 0]]
    print("Dither method: ordered (4 levels)\033[?25l")
    for row in tqdm(range(0, height)):
        for col in range(0, width):
            dotrow = 1 if row % 2 else 0
            dotcol = 1 if col % 2 else 0
            px = image.getpixel((col, row))
            new_pixels[col, row] = int(px > dots[dotrow][dotcol])
    return new


def ordered_dither_9(image: Image) -> Image:
    width, height = image.size
    new = new_image(width, height)
    new_pixels = new.load()
    dots = [[0, 196, 84], [168, 140, 56], [112, 28, 224]]
    print("Dither method: ordered (9 levels)\033[?25l")
    for row in tqdm(range(0, height)):
        for col in range(0, width):
            if not row % 3:
                dotrow = 2
            elif not row % 2:
                dotrow = 1
            else:
                dotrow = 0

            if not col % 3:
                dotcol = 2
            elif not col % 2:
                dotcol = 1
            else:
                dotcol = 0
            px = image.getpixel((col, row))
            new_pixels[col, row] = int(px > dots[dotrow][dotcol])
    return new


def threshold_dither(image: Image, threshold) -> Image:
    width, height = image.size
    new = new_image(width, height)
    new_pixels = new.load()
    if not threshold:
        px_list = list(image.getdata())
        threshold = sum(px_list) // len(px_list)
    print("Dither method: threshold (set to: {})\033[?25l".format(threshold))
    for row in tqdm(range(0, height)):
        for col in range(0, width):
            px = image.getpixel((col, row))
            new_pixels[col, row] = int(px > threshold)
    return new


def random_dither(image: Image, threshold: int) -> Image:
    width, height = image.size
    new = new_image(width, height)
    new_pixels = new.load()
    print("Dither method: random\033[?25l".format(threshold))
    for row in tqdm(range(0, height)):
        for col in range(0, width):
            px = image.getpixel((col, row))
            rand = randint(1, 255)
            new_pixels[col, row] = int(px > rand)
    return new


def error_diffusion_dither(image: Image) -> Image:
    width, height = image.size

    image_copy = image.copy()
    i = image_copy.load()

    new = new_image(width, height)
    new_pixels = new.load()
    print("Dither method: error diffusion\033[?25l")
    for row in tqdm(range(0, height)):
        for col in range(0, width):
            current = image_copy.getpixel((col, row))
            if current > 128:
                res = 1
                diff = -(255 - current)
            else:
                res = 0
                diff = abs(0 - current)
            mov = [[0, 1, 0.4375], [1, 1, 0.0625], [1, 0, 0.3125], [1, -1, 0.1875]]
            for x in mov:
                if row + x[0] >= height or col + x[1] >= width or col + x[1] <= 0:
                    continue
                p = image_copy.getpixel((col + x[1], row + x[0]))
                p = round(diff * x[2] + p)
                if p < 0:
                    p = 0
                elif p > 255:
                    p = 255
                i[col + x[1], row + x[0]] = p
            new_pixels[col, row] = res
    return new


def domain_checker(t: str, a: int, b: int) -> int:
    # domain [a, b]
    if not t.isnumeric(t) or not (a <= int(t) <= b):
        raise argparse.ArgumentTypeError(f"{t} not in domain [{a}, {b}]")
    return t


def path_checker(t: str) -> str:
    if not os.path.isfile(t):
        raise argparse.ArgumentTypeError(f"{t} not a valid path")
    return t


def main():
    parser = argparse.ArgumentParser(prog="lid", description="lid - lo-fi image dithering")

    parser.add_argument(
        "-f",
        choices=["jpeg", "jpg", "png", "gif"],
        default="png",
        help="output format. defaults to: png (recommended)",
    )
    parser.add_argument(
        "-m",
        default="o4",
        choices=["o4", "e", "o9", "t", "r", "a"],
        help="dither mode. defaults to: o4. other options: e, o9, t, r, a",
    )
    parser.add_argument(
        "-q",
        type=int,
        default=90,
        help="image quality. defaults to: 90. only has effect on png/jpg",
    )
    parser.add_argument(
        "-t",
        default=None,
        type=int,
        help="threshold. default: image average tone. onls has effect in mode 't'",
    )

    parser.add_argument(
        "infile", type=path_checker, help="path to a valid image file on your system"
    )
    parser.add_argument("outfile", help="path to a valid image file on your system")

    args = parser.parse_args()

    image = Image.open(str(args.infile)).convert("L")

    make_path = lambda s: Path(f"{args.outfile}_{s}.{args.f}")

    save_image(colorize(ordered_dither_4(image)), make_path("colorized"), args.q)
    return 
    match args.m:
        case "o4":
            save_image(ordered_dither_4(image), make_path("o4"), args.q)
        case "o9":
            save_image(ordered_dither_9(image), make_path("o9"), args.q)
        case "e":
            save_image(error_diffusion_dither(image), make_path("e"), args.q)
        case "t":
            save_image(threshold_dither(image, args.t), make_path("t"), args.q)
        case "r":
            save_image(random_dither(image, args.t), make_path("r"), args.q)
        case "a":
            save_image(ordered_dither_4(image), make_path("o4"), args.q)
            save_image(ordered_dither_9(image), make_path("o9"), args.q)
            save_image(threshold_dither(image, args.t), make_path("t"), args.q)
            save_image(error_diffusion_dither(image), make_path("e"), args.q)
            save_image(random_dither(image, args.t), make_path("r"), args.q)


if __name__ == "__main__":
    main()
