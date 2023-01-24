#!/usr/bin/env python3
# lid: lo-fi image dithering
# written by sloum, khoroo
# licence: public domain - use it, improve it, share it!
#########

import argparse
import os
import os.path
from random import randint
from typing import Optional

from PIL import Image


class Dither:
    def __init__(
        self, path: str, output_format: str, output_name: str, output_quality: int, threshold: int
    ):
        self.source_image = Image.open(path).convert("L")
        self.width, self.height = self.source_image.size
        self.pixel_count = self.width * self.height
        self.new = self.create_image()
        self.new_pixels = self.new.load()
        self.output_format = output_format
        self.output_name = output_name
        self.output_quality = output_quality
        self.threshold = threshold

        # used for printing progress
        self.counter = 1
        self.percent_val = 0
        self.hash_val = 0

    def save_file(self) -> None:
        output_filename = "{}.{}".format(self.output_name, self.output_format.lower())
        self.new.save(
            output_filename, self.output_format.upper(), optimize=True, quality=self.output_quality
        )
        print("\033[20C\nFinished! ~ {}/{}\033[?25h".format(os.getcwd(), output_filename))

    # Default dithering
    def ordered_dither_4(self) -> None:
        dots = [[64, 128], [192, 0]]
        print("Dither method: ordered (4 levels)\033[?25l")
        for row in range(0, self.height):
            for col in range(0, self.width):
                dotrow = 1 if row % 2 else 0
                dotcol = 1 if col % 2 else 0
                px = self.get_pixel(col, row)
                self.new_pixels[col, row] = int(px > dots[dotrow][dotcol])
                self.update_progress()
        self.save_file()

    def ordered_dither_9(self) -> None:
        dots = [[0, 196, 84], [168, 140, 56], [112, 28, 224]]
        print("Dither method: ordered (9 levels)\033[?25l")
        for row in range(0, self.height):
            for col in range(0, self.width):
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
                px = self.get_pixel(col, row)
                self.new_pixels[col, row] = int(px > dots[dotrow][dotcol])
                self.update_progress()
        self.save_file()

    def threshold_dither(self) -> None:
        if not self.threshold:
            px_list = list(self.source_image.getdata())
            self.threshold = sum(px_list) // len(px_list)
        print("Dither method: threshold (set to: {})\033[?25l".format(self.threshold))
        for row in range(0, self.height):
            for col in range(0, self.width):
                px = self.get_pixel(col, row)
                self.new_pixels[col, row] = int(px > self.threshold)
                self.update_progress()
        self.save_file()

    def random_dither(self) -> None:
        print("Dither method: random\033[?25l".format(self.threshold))
        for row in range(0, self.height):
            for col in range(0, self.width):
                px = self.get_pixel(col, row)
                rand = randint(1, 255)
                self.new_pixels[col, row] = int(px > rand)
                self.update_progress()
        self.save_file()

    def error_diffusion_dither(self) -> None:
        i = self.source_image.load()
        print("Dither method: error diffusion\033[?25l")
        for row in range(0, self.height):
            for col in range(0, self.width):
                self.new_pixels[col, row] = self.update_error(i, row, col)
                self.update_progress()
        self.save_file()

    # Helper for error_diffusion_dither
    def update_error(self, i: Image, r: int, c: int) -> int:
        current = self.get_pixel(c, r)
        if current > 128:
            res = 1
            diff = -(255 - current)
        else:
            res = 0
            diff = abs(0 - current)
        mov = [[0, 1, 0.4375], [1, 1, 0.0625], [1, 0, 0.3125], [1, -1, 0.1875]]
        for x in mov:
            if r + x[0] >= self.height or c + x[1] >= self.width or c + x[1] <= 0:
                continue
            p = self.get_pixel(c + x[1], r + x[0])
            p = round(diff * x[2] + p)
            if p < 0:
                p = 0
            elif p > 255:
                p = 255
            i[c + x[1], r + x[0]] = p
        return res

    def create_image(self) -> Image:
        return Image.new("1", (self.width, self.height))

    def get_pixel(self, col, row) -> Optional[int]:
        if col > self.width or row > self.height:
            return None
        return self.source_image.getpixel((col, row))

    def update_progress(self) -> None:
        self.counter += 1
        new_percent_val = round(self.counter / self.pixel_count * 100)
        new_hash_val = round(self.counter / self.pixel_count * 10)
        if new_percent_val != self.percent_val or new_hash_val != self.hash_val:
            print("\r{:>3}% |{:<10}|".format(new_percent_val, "#" * new_hash_val), end="")
            self.percent_val = new_percent_val
            self.hash_val = new_hash_val


def domain_checker(t: str, a: int, b: int) -> int:
    # domain [a, b]
    if not t.isnumeric(t) or not (a <= (ret := int(t)) <= b):
        raise argparse.ArgumentTypeError(f"{t} not in domain [{a}, {b}]")
    return ret


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
        type=lambda t: domain_checker(t, 1, 100),
        default=90,
        help="image quality. defaults to: 90. only has effect on png/jpg",
    )
    parser.add_argument(
        "-t",
        default=None,
        type=lambda t: domain_checker(t, 0, 255),
        help="threshold. default: image average tone. onls has effect in mode 't'",
    )

    parser.add_argument(
        "infile", type=path_checker, help="path to a valid image file on your system"
    )
    parser.add_argument("outfile", help="path to a valid image file on your system")

    args = parser.parse_args()

    d = Dither(args.infile, args.f, args.outfile, args.q, args.t)
    match args.m:
        case "o4":
            d.ordered_dither_4()
        case "09":
            d.ordered_dither_9()
        case "e":
            d.error_diffusion_dither()
        case "t":
            d.threshold_dither()
        case "r":
            d.random_dither()
        case "a":
            name = args.outfile
            d = Dither(args.infile, args.f, f"{name}_o4", args.q, args.t)
            d.ordered_dither_4()
            d2 = Dither(args.infile, args.f, f"{name}_o9", args.q, args.t)
            d2.ordered_dither_9()
            d3 = Dither(args.infile, args.f, f"{name}_t", args.q, args.t)
            d3.threshold_dither()
            d4 = Dither(args.infile, args.f, f"{name}_e", args.q, args.t)
            d4.error_diffusion_dither()
            d5 = Dither(args.infile, args.f, f"{name}_r", args.q, args.t)
            d5.random_dither()


if __name__ == "__main__":
    main()
