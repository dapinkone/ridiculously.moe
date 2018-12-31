# Frontend of an imageboard like wallhaven.cc.
# this file should outsource everything not delivering html/css.
from flask import (
    Flask, send_from_directory, render_template, redirect, abort, request
    )
from jinja2 import Template
import os
import sys
import json


app = Flask(__name__)
root = "/home/dap/projects/ridiculously.moe/"
img_dir = root + "img/"
thumbs_dir = img_dir + 'thumbs'
templates_dir = root + "templates/"
allowed_formats = ('JPG', 'JPEG', 'PNG')


# @PatchesPrime credit code @gw2api safeList
def safeList(ids, chunk_size):
    return [ids[x:x + chunk_size] for x in range(0, len(ids), chunk_size)]


@app.route('/img/<filename>')
def send_image_file(filename):
    try: #requires testing. possible security issue?
        return send_from_directory(img_dir, filename)
    except OSError as e:
        print(f"Error: unknown file {filename}", file=sys.stderr)
        abort(404)

@app.route('/img/thumbs/<filename>') # TODO: refactor sending files.
def send_thumb(filename):
    try:
        # doesn't matter. all our thumbs are png.
        basename, _ = os.path.splitext(filename);
        return send_from_directory(thumbs_dir, basename + '.png');
    except OSError as e:
        print(f"Error: unknown file {filename}", file=sys.stderr)
        abort(404)


@app.route('/wall/<img>')
def img_specific_page(img):
    base, _ = os.path.splitext(img)
    if os.path.isfile(os.path.join(img_dir, base + '.png')):
        ext = 'png'
    elif os.path.isfile(os.path.join(img_dir, base + '.jpg')):
        ext = 'jpg'
    else:
        abort(404)

    img = base + '.' + ext
    tags = []
    with open(os.path.join(img_dir, 'tags.json'), 'r') as tags_db:
        tags = json.load(tags_db)[base]
    return render_template("wall.html", img=img, tags=tags)

@app.route('/search')
def search():
    query = request.args.get('q', type= str)
    tags_query = query.lower().split('+')
    with open(os.path.join(img_dir + 'tags.json'), 'r') as db:
        tags_db = json.load(db)
        # https://i.ytimg.com/vi/MkmBNw1_jFw/maxresdefault.jpg
        matching_imgs = list()
        for name, img_tags in tags_db.items():
            if all(tag in {n.lower() for n in img_tags} for tag in tags_query):
                matching_imgs.append(name + ".png")
    return render_template("browse.html",
                           imgs=matching_imgs,
                           page=0,
                           max_page=0,
                           q=query
    ) # gonna need to change that template.



@app.route('/browse/<int:page>')
def thumbs_pg(page):
    if page < 0:  # no tricksy stuff in my math >:|
        return redirect("/browse/0")

    imgs = list()
    for img in os.listdir(img_dir):
        ext = os.path.splitext(img)[-1][1:].upper()  # :( slices pls
        if (ext in allowed_formats):
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
    elif words == 'script.js':
        return send_from_directory(templates_dir, 'script.js')
    else:
        abort(404)

@app.route('/') # a default drop page. TODO: add proper front page. #webdev
def index():
    tags = set()
    with open(os.path.join(img_dir, 'tags.json'), 'r') as tags_db:
        for _, img_tags in json.load(tags_db).items():
            tags.update(img_tags) # there has to be a better way ;_;
    return render_template("index.html", tags=list(tags))

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port="5000")
