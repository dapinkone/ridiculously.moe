# Frontend of an imageboard like wallhaven.cc.
# this file should outsource everything not delivering html/css.
from flask import (
    Flask, send_from_directory, render_template, redirect, abort, request
    )
from jinja2 import Template
import os
import sys
from pymongo import MongoClient


app = Flask(__name__)
root = "/home/dap/projects/ridiculously.moe/"
img_dir = root + "img/"
thumbs_dir = img_dir + 'thumbs'
templates_dir = root + "templates/"
css_dir = root + "css/"
allowed_formats = ('JPG', 'JPEG', 'PNG')

class My_db:
    def __init__(self):
        self.db = MongoClient('192.168.1.41').moe

    def get_imgs_by_tag(self, q):
        result = self.db.images.find(
            {"tags": {"$all": list(q)}})
        match_names = list()
        for entry in result:
            match_names.append(entry['name'])
        return match_names

    def get_img_struct(self, img_name):
        return self.db.images.find_one(
            {"name": {"$all": [img_name]}})

    def get_random_selection(self, how_many):
        result = self.db.images.aggregate(
            [{ "$sample": { "size": how_many }}])
        return [entry['name'] for entry in result]

mongodb = My_db()


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

    img_data = mongodb.get_img_struct(base)
    return render_template("wall.html", img=img, tags=img_data['tags'])

@app.route('/search')
def search():
    query = request.args.get('q', type= str)
    tags_query = query.split('+')

    results = mongodb.get_imgs_by_tag(tags_query)
    return render_template("browse.html",
                           imgs=results,
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
        img_base, ext = os.path.splitext(img)

        if (ext[1:].upper() in allowed_formats):
            imgs.append(img_base)

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


@app.route('/<string:filename>')
def return_style(filename):
    # hacky. needs serious reconsideration to be more meta.
    base, ext = os.path.splitext(filename)
    if ext == '.css':
        return send_from_directory(css_dir, filename)
    if filename == 'script.js':
        return send_from_directory(templates_dir, 'script.js')
    else:
        abort(404)

@app.route('/') # a default drop page. TODO: add proper front page. #webdev
def index():
    # tags = set()
    # return render_template("index.html", tags=list(tags))
    return redirect('/random')


@app.route('/random')
def random():
    return render_template("random.html",
                           imgs=mongodb.get_random_selection(15))

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port="5000")
