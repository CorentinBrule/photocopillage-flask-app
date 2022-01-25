from flask import Flask, render_template, send_from_directory, request, url_for, flash, redirect, jsonify
from flask_weasyprint import HTML, render_pdf
import json
from datetime import datetime
from cover import overlay_image
import os
from celery import Celery
import numpy
import cv2
import logging
import sys
logging.basicConfig(level=logging.DEBUG)


match_threshold = 10000000

app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

with open("photocopillage.data.json", "r") as f:
    DATA = json.load(f)


def filter_data(data, match_threshold):
    enable_data = []
    for document in data:
        page_counter = 0
        for page in document.get("pages", []):
            available = page.get("available", True)
            if available:
                match = page.get("match")
                if match.get("value") > match_threshold:
                    page_counter += 1
        if page_counter == 1:  # seulement si il y a qu'une page dispo et qui match
            enable_data.append(document)
    return enable_data


def sort_data(data, way_of_sorting):
    if way_of_sorting == "byIndexationDate":
        return sorted(data, key=lambda k: datetime.strptime(k['first_indexation_date'], '%d/%m/%Y'))
    if way_of_sorting == "byPublishingDate":
        pass


def split_data(data, chunk_size, chunk_part=0):
    if chunk_size == 0:
        return data
    else:
        return data[chunk_part * chunk_size:(chunk_part + 1) * chunk_size]

def mm2in(value):
    return value / 25.4

@celery.task(bind=True)
def create_cover_images_background(self, images_folder, enable_data, page_width, page_height, scale, chunk_size, chunk_part, output_folder, cover_names):
    start_vol = chunk_part*chunk_size
    end_vol = min(start_vol + chunk_size,len(DATA))
    N = end_vol - start_vol

    message = ""
    print(scale, file=sys.stdout)
    app.logger.info("coucou")
    app.logger.info(scale)
    # Create a numpy array of integers to store the average
    # arrRight = numpy.zeros((h, w), numpy.uint8) # gray scale
    # arrLeft = numpy.zeros((h, w), numpy.uint8)
    cover1 = numpy.zeros((int(page_height), int(page_width), 3), numpy.float)  # color
    cover4 = numpy.zeros((int(page_height), int(page_width), 3), numpy.float)

    for i, document in enumerate(enable_data):
        for logo_page in document["pages"]:
            if logo_page.get("available", True):
                #print(document["id"])
                targetX, targetY = logo_page["match"]["center"]
                if not scale == 1.0:
                    print("rescale")
                    print(targetX)
                    print(targetY)
                    targetX = int(targetX * scale)
                    targetY = int(targetY * scale)
                    print(targetX)
                    print(targetY)
                offsetX = int(page_width/2 - targetX)
                offsetY = int(page_height/2 - targetY)

                # cover 1 --> logos
                logo_path = images_folder + "/" + document["id"] + "-f" + logo_page["pagination"] + ".jpg"
                logo_img = cv2.imread(logo_path)
                if not scale == 1.0:
                    print((logo_img.shape[1], logo_img.shape[0]))
                    dsize = (int(logo_img.shape[1] * scale), int(logo_img.shape[0] * scale))
                    print(dsize)
                    logo_img = cv2.resize(logo_img, dsize)

                tmp_cover1 = numpy.zeros((page_height, page_width, 3), numpy.float)
                overlay_image(tmp_cover1, logo_img, offsetX, offsetY)

                # cover 4 --> covers
                cover_path = images_folder + "/" + document["id"]+".jpg"
                cover_img = cv2.imread(cover_path)
                print(scale)
                if not scale == 1.0:
                    dsize = (int(cover_img.shape[1] * scale), int(cover_img.shape[0] * scale))
                    cover_img = cv2.resize(cover_img, dsize)

                tmp_cover4 = numpy.zeros((page_height, page_width, 3), numpy.float)
                overlay_image(tmp_cover4, cover_img, offsetX, offsetY)

                # opacity for average
                cover1 = cover1 + tmp_cover1 / N
                cover4 = cover4 + tmp_cover4 / N
                message = "{} images sur {}".format(i, N)
                self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': N,
                                'status': message})
                #
                # if i % 100 == 0:
                #     cover1_name = "photocopillage-by"+str(chunk_size)+"-"+str(chunk_part)+"-cover1.png"
                #     cover4_name = "photocopillage-by"+str(chunk_size)+"-"+str(chunk_part)+"-cover4.png"
                #     cv2.imwrite(output_folder + cover1_name, cover1)
                #     cv2.imwrite(output_folder + cover4_name, cover4)

    cover1_name = cover_names[0]
    cover4_name = cover_names[1]
    cv2.imwrite(output_folder + cover1_name, cover1)
    cv2.imwrite(output_folder + cover4_name, cover4)

    images_name = (cover1_name, cover4_name)

    return {'current': N, 'total': N, 'status': 'Task completed!',
            'result': images_name}


@app.route('/longtask', methods=['POST'])
def longtask():
    task = create_cover_images_background.apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}


W = 7
H = 10
bleed = 0.125
pageWidth = W + bleed * 2
pageHeight = H + bleed * 2

book = {
    "width": W,
    "height": H,
    "bleed": bleed,
    "scale": 1.0,
    "dpi": 400,
    "noscript": False,
    "chunk_size": 0,
    "chunk_part": 0,
    "pages_per_inch": 444,
    "sort": "byIndexationDate"
}


@app.route('/')
def index():
    enable_data = filter_data(DATA, match_threshold)
    enable_data = sort_data(enable_data, "byIndexationDate")
    return send_from_directory('static','photocopillage-all.html')


@app.route('/chunk')
def chunk():
    book['width'] = mm2in(float(request.args.get("width")))
    book['height'] = mm2in(float(request.args.get("height")))
    book['scale'] = float(request.args.get("scale", 1.0))
    book['chunk_size'] = int(request.args.get("chunk-size"))
    book['chunk_part'] = int(request.args.get("chunk-part"))-1
    book['sort'] = request.args.get("sort", type=str)
    enable_data = filter_data(DATA, match_threshold)
    enable_data = sort_data(enable_data, book['sort'])
    enable_data = split_data(enable_data,  book['chunk_size'], book['chunk_part'])

    return render_template('book.html', documents=enable_data, book=book)


# @app.route('/book/<way_of_sorting>/<int:threshold>/<width>/<height>/<bleed>/<scale>/<int:dpi>', methods=('GET', 'POST'))
# def param_book(way_of_sorting, threshold, width, height, bleed, scale, dpi):
#     enable_data = filter_data(DATA, threshold)
#     enable_data = sort_data(enable_data, way_of_sorting)
#
#     book['width'] = float(width)
#     book['height'] = float(height)
#     book['bleed'] = float(bleed)
#     book['scale'] = float(scale)
#     book['dpi'] = int(dpi)
#
#     return render_template('book.html', documents=enable_data, book=book)


@app.route('/chunk/<int:chunk_size>/<int:chunk_part>/noscript=<int:noscript>', methods=('GET', 'POST'))
@app.route('/chunk/<int:chunk_size>/<int:chunk_part>', methods=('GET', 'POST'))
def chunk_route(chunk_size, chunk_part, noscript=0):
    enable_data = filter_data(DATA, match_threshold)
    enable_data = sort_data(enable_data, "byIndexationDate")
    enable_data = split_data(enable_data, chunk_size, chunk_part)
    book["chunk_size"] = chunk_size
    book["chunk_part"] = chunk_part
    book["noscript"] = bool(noscript)
    return render_template('book.html', documents=enable_data, book=book)


@app.route('/chunk/<int:chunk_size>/<int:chunk_part>.pdf')
def chunk_pdf(chunk_size, chunk_part):
    enable_data = filter_data(DATA, match_threshold)
    enable_data = sort_data(enable_data, "byIndexationDate")
    enable_data = split_data(enable_data, chunk_size, chunk_part)
    book["chunk_size"] = chunk_size
    book["chunk_part"] = chunk_part
    book["noscript"] = True
    print(book)
    html = render_template('book.html', documents=enable_data, book=book)
    # print(html)
    return render_pdf(HTML(string=html))


# @app.route('/chunk/<int:chunk_size>/<int:chunk_part>/cover', methods=('GET', 'POST'))
# def chunk_cover(chunk_size, chunk_part):
#     enable_data = filter_data(DATA, match_threshold)
#     enable_data = sort_data(enable_data, "byIndexationDate")
#     enable_data = split_data(enable_data, chunk_size, chunk_part)
#     page_width_pixel = int(book["width"] + book["bleed"] * 2) * book["dpi"]
#     page_height_pixel = int(book["height"] + book["bleed"] * 2) * book["dpi"]
#     scale = book['scale']
#     book["chunk_size"] = chunk_size
#     book["chunk_part"] = chunk_part
#     task = False
#     cover1_name = "photocopillage-" + str(book['width']).replace(".","_") + "-" + str(book['height']).replace(".","_") + "-" + str(book['scale']).replace(".","_") + "-" + str( book['chunk_size']) + "-" + str(book['chunk_part']) + "-cover1.png"
#     cover4_name = "photocopillage-" + str(book['width']).replace(".","_") + "-" + str(book['height']).replace(".","_") + "-" + str(book['scale']).replace(".","_") + "-" + str( book['chunk_size']) + "-" + str(book['chunk_part']) + "-cover4.png"
#     cover_names = (cover1_name, cover4_name)
#
#     covers_path = os.path.join(APP_ROOT, "static/covers/")
#     #print(enable_data)
#     if os.path.isfile(covers_path + cover1_name) and os.path.isfile(covers_path + cover4_name):
#         task = 0
#     else:
#         task = create_cover_images_background.apply_async(args=[os.path.join(APP_ROOT, "static/images/"),
#                                                          enable_data,
#                                                          page_width_pixel,
#                                                          page_height_pixel,
#                                                          scale,
#                                                          chunk_size,
#                                                          chunk_part,
#                                                          covers_path,
#                                                          cover_names])
#
#     return render_template('cover.html', documents=enable_data, book=book, cover_names=cover_names,task=task)


@app.route('/cover', methods=('GET','POST'))
def chunk_cover2():
    book['width'] = mm2in(float(request.args.get("width", book['width'])))
    book['height'] = mm2in(float(request.args.get("height", book['height'])))
    book['scale'] = float(request.args.get("scale", 1.0))
    book['chunk_size'] = int(request.args.get("chunk-size"))
    book['chunk_part'] = int(request.args.get("chunk-part"))-1
    book['sort'] = request.args.get("sort", book['sort'], type=str)
    print(book['scale'])

    enable_data = filter_data(DATA, match_threshold)
    enable_data = sort_data(enable_data, book['sort'])
    enable_data = split_data(enable_data,  book['chunk_size'], book['chunk_part'])

    page_width_pixel = int(book["width"] + book["bleed"] * 2) * book["dpi"]
    page_height_pixel = int(book["height"] + book["bleed"] * 2) * book["dpi"]

    task = False
    cover1_name = "photocopillage-" + str(book['width']).replace(".","_") + "-" + str(book['height']).replace(".","_") + "-" + str(book['scale']).replace(".","_") + "-" + str( book['chunk_size']) + "-" + str(book['chunk_part']) + "-cover1.png"
    cover4_name = "photocopillage-" + str(book['width']).replace(".","_") + "-" + str(book['height']).replace(".","_") + "-" + str(book['scale']).replace(".","_") + "-" + str( book['chunk_size']) + "-" + str(book['chunk_part']) + "-cover4.png"
    cover_names = (cover1_name, cover4_name)

    covers_path = os.path.join(APP_ROOT, "static/covers/")
    #print(enable_data)
    if os.path.isfile(covers_path + cover1_name) and os.path.isfile(covers_path + cover4_name):
        task = 0
    else:
        task = create_cover_images_background.apply_async(args=[os.path.join(APP_ROOT, "static/images/"),
                                                         enable_data,
                                                         page_width_pixel,
                                                         page_height_pixel,
                                                         book['scale'],
                                                         book['chunk_size'],
                                                         book['chunk_part'],
                                                         covers_path,
                                                         cover_names])

    return render_template('cover-server.html', documents=enable_data, book=book, cover_names=cover_names,task=task)

@app.route('/cover-client', methods=('GET','POST'))
def chunk_cover3():
    book['width'] = mm2in(float(request.args.get("width", book['width'])))
    book['height'] = mm2in(float(request.args.get("height", book['height'])))
    book['scale'] = float(request.args.get("scale", 1.0))
    book['chunk_size'] = int(request.args.get("chunk-size"))
    book['chunk_part'] = int(request.args.get("chunk-part"))-1
    book['sort'] = request.args.get("sort", book['sort'], type=str)
    print(book['scale'])

    enable_data = filter_data(DATA, match_threshold)
    enable_data = sort_data(enable_data, book['sort'])
    enable_data = split_data(enable_data,  book['chunk_size'], book['chunk_part'])

    page_width_pixel = int(book["width"] + book["bleed"] * 2) * book["dpi"]
    page_height_pixel = int(book["height"] + book["bleed"] * 2) * book["dpi"]

    task = False
    cover1_name = "photocopillage-" + str(book['width']).replace(".","_") + "-" + str(book['height']).replace(".","_") + "-" + str(book['scale']).replace(".","_") + "-" + str( book['chunk_size']) + "-" + str(book['chunk_part']) + "-cover1.png"
    cover4_name = "photocopillage-" + str(book['width']).replace(".","_") + "-" + str(book['height']).replace(".","_") + "-" + str(book['scale']).replace(".","_") + "-" + str( book['chunk_size']) + "-" + str(book['chunk_part']) + "-cover4.png"
    cover_names = (cover1_name, cover4_name)

    covers_path = os.path.join(APP_ROOT, "static/covers/")
    #print(enable_data)
    if os.path.isfile(covers_path + cover1_name) and os.path.isfile(covers_path + cover4_name):
        task = 0
    else:
        task = 1

    return render_template('cover-client.html', documents=enable_data, book=book, cover_names=cover_names,task=task)


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = create_cover_images_background.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

@app.route("/response", methods=('GET', 'POST'))
def response():
    book['width'] = mm2in(float(request.args.get("width")))
    book['height'] = mm2in(float(request.args.get("height")))
    book['scale'] = float(request.args.get("scale", 1))
    book['chunk_size'] = int(request.args.get("chunk-size"))
    book['chunk_part'] = int(request.args.get("chunk-part"))-1
    book['sort'] = request.args.get("sort", type=str)
    enable_data = filter_data(DATA, match_threshold)
    enable_data = sort_data(enable_data, book['sort'])
    enable_data = split_data(enable_data,  book['chunk_size'], book['chunk_part'])

    return render_template('response.html', documents=enable_data, book=book)



# debuger log
@app.context_processor
def utility_functions():
    def print_in_console(message):
        print(str(message))

    return dict(debug=print_in_console)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
