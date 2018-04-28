from flask import Flask, send_from_directory, render_template, redirect, abort
from jinja2 import Template
import os
import sys
from PIL import Image
import dhash
import json

dhash.force_pil()  # force use PIL, not wand/imagemagick

app = Flask(__name__)
root = "/home/dap/projects/ridiculously.moe/"
img_dir = root + "img/"
templates_dir = root + "templates/"
allowed_formats = ('JPG', 'JPEG', 'PNG')


# @PatchesPrime credit code @gw2api safeList
def safeList(ids, chunk_size):
    return [ids[x:x + chunk_size] for x in range(0, len(ids), chunk_size)]


def get_dhash(filename):
    # given a filename, return the dhash of the image
    with Image.open(filename) as img:
        # adjust size for senstivity. greater size==more senstivity
        # results of testing for dups on my collection:
        # 215 detected @ s=8; 160@16; 160@32;
        img_dhash = dhash.dhash_int(img, size=16)
        return(img_dhash)


def mk_thumbnail(filename):
    f, ext = os.path.splitext(filename)
    ext = ext[1:].upper()  # all my wat at '.png'
    if 'th-' in f or os.path.isfile(img_dir + 'th-' + filename):
        return   # >_> this could be nicer.

    im = Image.open(img_dir + filename)
    im.thumbnail((300, 200))

    if ext in allowed_formats:
        if ext == 'JPG':
            ext = 'JPEG'

        im.save(img_dir + 'th-' + filename, ext)
        print('Converted ' + filename + ' to thumbnail.')
    else:
        print('Failed to build thumbnail: unknown file extension ' + ext,
              file=sys.stderr
              )


@app.route('/img/<filename>')
def send_image_file(filename):
    if all([not os.path.isfile(img_dir + filename),
            filename.startswith('th-'),
            os.path.isfile(img_dir + filename[3:])
            ]):
        mk_thumbnail(filename[3:])
    try:
        return send_from_directory(img_dir, filename)
    except OSError as e:
        print(f"Error: unknown file {filename}", file=sys.stderr)
        abort(404)


@app.route('/browse/<string:words>')
def redir_to_browse(words):  # maybe this will be browse-by-tag later?
    return redirect("/browse/0")


@app.route('/browse/<int:page>')
def thumbs_pg(page):
    if page < 0:  # no tricksy stuff in my math >:|
        return redirect("/browse/0")

    imgs = list()
    for img in os.listdir(img_dir):
        ext = os.path.splitext(img)[-1][1:].upper()  # :( slices pls
        if (ext in allowed_formats) and (not img.startswith('th-')):
            imgs.append(img)

    # chunk list of imgs into pages of 30 each, and select our page
    pages = safeList(imgs, 30)
    try:
        curr_page_imgs = pages[page]
    except IndexError:
        abort(404)

    # forward the list of imgs into the jinja template
    # I'd rather pass in a dict, but I guess jinja2 doesn't do that?
    return render_template("browse.html",
                           imgs=curr_page_imgs,
                           page=page,
                           max_page=len(pages)-1)


@app.route('/<string:words>')
def return_style(words):
    # hacky. needs serious reconsideration to be more meta.
    if words == 'styles.css':
        return send_from_directory(templates_dir, 'styles.css')
    else:
        abort(404)
