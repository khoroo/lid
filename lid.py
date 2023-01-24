#!/usr/bin/env python3
# lid: lo-fi image dithering
# written by sloum
# licence: public domain - use it, improve it, share it!
#########

from PIL import Image
import sys
import os, os.path
from random import randint

class Dither:
    def __init__(self, data):
        self.source_image = Image.open(data["path"]).convert("L")
        self.width, self.height = self.source_image.size
        self.pixel_count = self.width * self.height
        self.new = self.create_image()
        self.new_pixels = self.new.load()
        self.output_format = data["-f"]
        self.output_name = data["out"]
        self.output_quality = data["-q"]
        self.threshold = data["-t"]

        #used for printing progress
        self.counter = 1
        self.percent_val = 0
        self.hash_val = 0


    def save_file(self):
        output_filename = "{}.{}".format(self.output_name, self.output_format.lower())
        self.new.save(output_filename, self.output_format.upper(), optimize=True, quality=self.output_quality)
        print("\033[20C\nFinished! ~ {}/{}\033[?25h".format(os.getcwd(), output_filename))


    # Default dithering
    def ordered_dither_4(self):
        dots = [[64, 128],[192, 0]]
        print("Dither method: ordered (4 levels)\033[?25l")
        for row in range(0, self.height):
            for col in range(0, self.width):
                dotrow = 1 if row % 2 else 0
                dotcol = 1 if col % 2 else 0
                px = self.get_pixel(col, row)
                self.new_pixels[col, row] = int(px > dots[dotrow][dotcol])
                self.update_progress()
        self.save_file()


    def ordered_dither_9(self):
        dots = [
            [0, 196, 84],
            [168, 140, 56],
            [112, 28, 224]
        ]
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


    def threshold_dither(self):
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


    def random_dither(self):
        print("Dither method: random\033[?25l".format(self.threshold))
        for row in range(0, self.height):
            for col in range(0, self.width):
                px = self.get_pixel(col, row)
                rand = randint(1,255)
                self.new_pixels[col, row] = int(px > rand)
                self.update_progress()
        self.save_file()

    def error_diffusion_dither(self):
        i = self.source_image.load()
        print("Dither method: error diffusion\033[?25l")
        for row in range(0, self.height):
            for col in range(0, self.width):
                self.new_pixels[col, row] = self.update_error(i, row, col)
                self.update_progress()
        self.save_file()


    # Helper for error_diffusion_dither
    def update_error(self, i, r, c):
        current = self.get_pixel(c, r)
        if current > 128:
            res = 1
            diff = -(255 - current)
        else:
            res = 0
            diff = abs(0 - current)
        mov = [[0, 1, 0.4375],[1, 1, 0.0625],[1, 0, 0.3125],[1, -1, 0.1875]]
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


    # Create a new image with the given size
    def create_image(self):
        image = Image.new("1", (self.width, self.height))
        return image


    # Get the pixel from the given image
    def get_pixel(self, col, row):
        if col > self.width or row > self.height:
            return None

        # Get Pixel
        pixel = self.source_image.getpixel((col, row))
        return pixel


    def update_progress(self):
        self.counter += 1
        new_percent_val = round(self.counter / self.pixel_count * 100)
        new_hash_val = round(self.counter / self.pixel_count * 10)
        if new_percent_val != self.percent_val or new_hash_val != self.hash_val:
            print("\r{:>3}% |{:<10}|".format(new_percent_val, "#" * new_hash_val), end="")
            self.percent_val = new_percent_val
            self.hash_val = new_hash_val


#---- END Dither class ----#


def display_help():
    helptext = """
    lid - lo-fi image dithering

    syntax:
    lid [option]... [infile] [outfile]

    options:
    -f          output format. defaults to: png (recommended)
    -m          dither mode. defaults to: o4. other options: e, o9, t, r, a
    -q          image quality. defaults to: 90. only has effect on png/jpg
    -t          threshold. default: image average tone. onls has effect in mode 't'

    arguments:
    infile      path to a valid image file on your system
    outfile     file name to output, do not include file extension

    example usage:
    lid -f jpeg -q 75 -m e ~/my_picture.png my_dithered_picture

    notes:
    it is highly recommended that users output their files as PNG. the file
    size will be significantly smaller than jpeg and the quality in most
    cases will be about the same.

    the quality flag mostly seems to effect jpegs and does not do a whole
    heap to PNG files, but play around with it as mileage may vary.

    to output an image with each type of dither, use mode a
    """
    print(helptext)


# Get and validate the arguments
# returns dict or None
def parse_input():
    args = sys.argv[1:]
    argmap = {
        "-f": "png",       # output format
        "-q": 25,          # optimization quality
        "-m": "o4",        # mode, defaults to ordered
        "-t": None,         # threshold
        "path": None,      # path to file
        "out": "lid_file"  # output filename
    }
    if len(args) < 1:
        print("lid error: expected image filepath, received None")
        return None

    if "help" in args or "-h" in args or "--help" in args:
        display_help()
        sys.exit(1)

    item = None
    for x in args:
        if x in argmap:
            item = x
            continue
        elif item:
            argmap[item] = x
            item = None
        elif len(x) > 0 and x[0] == "-":
            print("lid error: unknown flag {}".format(x))
            return None
        else:
            if argmap["path"]:
                argmap["out"] = x
            else:
                argmap["path"] = x

    if not argmap["-f"].lower() in ["jpeg", "jpg", "png", "gif"]:
        print("lid error: invalid format requested with -f flag. Options: jpeg, png, gif. Defaults to png")
        return None
    elif argmap["-f"] == "jpg":
        argmap["-f"] = "jpeg"

    if not argmap["-m"] in ["o4", "e", "o9", "t", "r", "a"]:
        print("lid error: invalid dither mode provided for -m. Options: o4, o9, e, t, r, a. Default: o4")
        return None

    try:
        if argmap["-t"]:
            argmap["-t"] = int(argmap["-t"])
            if argmap["-t"] < 0 or argmap["-t"] > 255:
                print("lid error: threshold value must be between 0 and 255")
                return None
    except ValueError:
        print("lid error: invalid threshold value provided for -m. Must be integer from 0 to 255")
        return None

    try:
        argmap["-q"] = int(argmap["-q"])
        if argmap["-q"] < 1 or argmap["-q"] > 100:
            print("lid error: -q value must be between 1 and 100")
            return None
    except ValueError:
        print("lid error: -q value must be an integer")
        return None

    if not argmap["path"] or not os.path.isfile(argmap["path"]):
        print("lid error: invalid filepath")
        return None

    return argmap

def main():
    request = parse_input()
    if request:
        d = Dither(request)
        if request["-m"] == "o4":
            d.ordered_dither_4()
        elif request["-m"] == "o9":
            d.ordered_dither_9()
        elif request["-m"] == "e":
            d.error_diffusion_dither()
        elif request["-m"] == "t":
            d.threshold_dither()
        elif request["-m"] == "r":
            d.random_dither()
        elif request["-m"] == "a":
            name = request["out"]
            request["out"] = name + "_o4"
            d = Dither(request)
            d.ordered_dither_4()
            request["out"] = name + "_o9"
            d2 = Dither(request)
            d2.ordered_dither_9()
            request["out"] = name + "_t"
            d3 = Dither(request)
            d3.threshold_dither()
            request["out"] = name + "_e"
            d4 = Dither(request)
            d4.error_diffusion_dither()
            request["out"] = name + "_r"
            d4 = Dither(request)
            d4.random_dither()
        else:
            print("Unknown mode flag")
            sys.exit(2)
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
