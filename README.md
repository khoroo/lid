# Lid
_lo-fi image dithering_

Lid performs fairly basic 1 bit image dithering. It converts an input image to grayscale and then dithers that image. It then optimizes the output and saves the file. The result is a reduced filesize, simple image, great for small page sizes.

## Dependencies

- Python3.x (built and tested with 3.6)
- PIL (python3 -m pip install Pillow)

## Documentation

lid [option]... [source path] [output name]

Options:<br>
-f = output format, defaults to the recommended setting: png<br>
-m = mode, available: o4, o9, e, t, r, a. default: o4.<br>
-q = quality (0 - 100), defaults to 90, only affects jpeg/jpg<br>
-t = threshold (0 - 255), defaults to image average level. only affects dither mode 't'

source path = a path to an image file you want to dither<br>
output name = the name of the file you would like to output, do not include file extension

Lid works best outputting png files from any input. You will get the smallest file with the best quality this way.

### Modes

#### t
This is the lowest quality mode. It produces the smallest file, but at the cost of most detail.

#### r
Random dithering produces a fairly large file (comparable to error diffusion), without moving much closer to photographic quality. However, it does provide an interesting effect.

#### o4
This mode is a noticable difference from the stark two tone appearance of threashold mode. The appearance 'gray' areas make for a slightly more photographic image.

#### o9
This mode produces medium quality dithering, it is still a very noticeable effect but not as harsh as o4. It is a nine level ordered dither.

#### e
This is the highest quality mode. It uses an error diffusion dither. The file size will be the largest of the bunch, but should still be a good reduction from a regular full color photograph.

#### a
The a, or all, mode is a quick flag to say that you want an image put out in all of the modes. The mode flag value for each will be appended to the filename.

## License
Public domain. Use it, improve it, share it!
