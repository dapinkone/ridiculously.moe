# watches images directory for new files.
# makes thumbnails on demand
from PIL import Image
import os
import time
import sys

allowed_formats = ('JPG', 'JPEG', 'PNG')


def mk_thumbnail(img_dir, filename):
    basename, ext = os.path.splitext(filename)
    ext = ext[1:].upper()  # all my wat at '.png'

    if ext.upper() in allowed_formats:
        if ext == 'JPG':
            ext = 'JPEG'

        im = Image.open(os.path.join(img_dir, filename))
        im.thumbnail((300, 200))

        th_fullpath = os.path.join(img_dir + "thumbs", basename + '.png')

        im.save(th_fullpath, ext)
        print('Converted ' + filename + ' to thumbnail.')
    else:
        print('Failed to build thumbnail: unknown file extension ' + ext,
              file=sys.stderr
              )


if __name__ == '__main__':
    img_dir = '/home/dap/projects/ridiculously.moe/img/'

    while True:
        found_new = None
        for img_filename in os.listdir(img_dir):
            if img_filename.startswith('th-'):  # this is already a thumbnail.
                continue
            img_ext = os.path.splitext(img_filename)[1][1:]

            if img_ext.upper() not in allowed_formats:
                continue  # that's not an image!

            if not os.path.isfile(os.path.join(img_dir, "th-" + img_filename)):
                # we don't have a thumbnail for this one.
                try:
                    mk_thumbnail(img_dir, img_filename)
                    found_new = True
                except OSError as e:
                    # sometimes we're too fast, so the file isn't done
                    # being written.
                    if "not processed" in str(e):
                        pass # >.>
                    else:
                        raise OSError(e)

        if found_new:
            print('--')
            found_new = None

        time.sleep(1)
