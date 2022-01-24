import argparse
import numpy
import os
# from PIL import Image
# import pdf2image
import json
from datetime import datetime
import cv2

def split_data(data, chunk_size, chunk_part=0):
    if chunk_size == 0:
        return data
    else:
        return data[chunk_part * chunk_size:(chunk_part+1)*chunk_size]


def overlay_image(img, img_overlay, x, y):
    """Overlay `img_overlay` onto `img` at (x, y) and blend using `alpha_mask`.

    `alpha_mask` must have same HxW as `img_overlay` and values in range [0, 1].
    """
    # Image ranges
    y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
    x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

    # Overlay ranges
    y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
    x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

    # Exit if nothing to do
    if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
        return

    # Blend overlay within the determined ranges
    img_crop = img[y1:y2, x1:x2]
    img_overlay_crop = img_overlay[y1o:y2o, x1o:x2o]
    #alpha = alpha_mask[y1o:y2o, x1o:x2o, numpy.newaxis]
    #alpha_inv = 1.0 - alpha

    #img_crop[:] = alpha * img_overlay_crop + alpha_inv * img_crop
    img_crop[:] = img_overlay_crop


def progress():
    for i in range(10):
        yield i


def create_cover_images(images_folder, data, page_width, page_height, scale, chunk_size, chunk_part, output_folder):

    start_vol = chunk_part*chunk_size
    end_vol = start_vol+len(data)
    N = end_vol - start_vol

    # Create a numpy array of integers to store the average
    # arrRight = numpy.zeros((h, w), numpy.uint8) # gray scale
    # arrLeft = numpy.zeros((h, w), numpy.uint8)
    cover1 = numpy.zeros((page_height, page_width, 3), numpy.float)  # color
    cover4 = numpy.zeros((page_height, page_width, 3), numpy.float)

    for i, document in enumerate(data):
        for logo_page in document["pages"]:
            if logo_page.get("available", True):
                #print(document["id"])
                targetX, targetY = logo_page["match"]["center"]
                if not scale == 1.0:
                    targetX = int(targetX * scale)
                    targetY = int(targetY * scale)
                offsetX = int(page_width/2 - targetX)
                offsetY = int(page_height/2 - targetY)

                cover_path = images_folder + "/" + document["id"]+".jpg"

                cover_img = cv2.imread(cover_path)
                if not scale == 1.0:
                    dsize = (int(cover_img.shape[1] * scale), int(cover_img.shape[0] * scale))
                    cv2.resize(cover_img, dsize)

                tmp_cover1 = numpy.zeros((page_height, page_width, 3), numpy.float)
                overlay_image(tmp_cover1, cover_img, offsetX, offsetY)

                logo_path = images_folder + "/" + document["id"] + "-f" + logo_page["pagination"] + ".jpg"
                logo_img = cv2.imread(logo_path)
                if not scale == 1.0:
                    dsize = (int(logo_img.shape[1] * scale), int(logo_img.shape[0] * scale))
                    cv2.resize(logo_img, dsize)

                tmp_cover4 = numpy.zeros((page_height, page_width, 3), numpy.float)
                overlay_image(tmp_cover4, logo_img, offsetX, offsetY)
                # opacity for average
                cover1 = cover1 + tmp_cover1 / N
                cover4 = cover4 + tmp_cover4 / N

    cover1_name = "photocopillage-by"+str(chunk_size)+"-"+str(chunk_part)+"-cover1.png"
    cover4_name = "photocopillage-by"+str(chunk_size)+"-"+str(chunk_part)+"-cover4.png"
    cv2.imwrite(output_folder + cover1_name, cover1)
    cv2.imwrite(output_folder + cover4_name, cover4)
    return cover1_name, cover4_name


if __name__=="__main__" :
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--images", help="Path of page image")
    parser.add_argument("-c", "--chunk", help="Pages by vol", type=int)
    parser.add_argument("-p", "--part", help="Number of vol", type=int)
    parser.add_argument("-o", "--output",help="output folder path")
    parser.add_argument("-s", "--spine", type=float)
    parser.add_argument("--scale",type=float)
    parser.add_argument("--data")
    #parser.add_argument("--pdf", help="pdf of book", nargs="+")

    args = parser.parse_args()

    images_folder = ""
    pdf_files = []
    ppi = 400
    W = 7
    H = 10
    bleed = 0.125 # fonds perdus
    start_vol = 0
    end_vol = False
    spine = 0.5
    scale = 1.0
    match_threshold = 10000000
    output_folder = "static/covers/"

    if args.images is not None:
        images_folder = args.images
    if args.chunk is not None:
        chunk = args.chunk
    if args.part is not None:
        part = args.part
    if args.spine is not None:
        spine = args.spine
    if args.scale is not None:
        scale = args.scale
    if args.output is not None:
        output_folder = args.output
    if args.data is not None:
        with open(args.data,'r') as f:
            data = json.load(f)


    page_width = int((W + bleed * 2) * ppi)
    page_height = int((H + bleed * 2) * ppi)

    enable_data = []

    for document in data:
        page_counter = 0
        for page in document.get("pages", []):
            available = page.get("available", True)
            if available:
                match = page.get("match")
                if match.get("value") > match_threshold:
                    page_counter += 1
        if page_counter == 1:  # seulement si il y a qu'une page "available" et qui match
            enable_data.append(document)

    enable_data = sorted(enable_data, key=lambda k: datetime.strptime(k['first_indexation_date'], '%d/%m/%Y'))
    enable_data = split_data(enable_data)

    cover_paths = create_cover_images(images_folder, enable_data, page_width, page_height, scale, chunk, part, output_folder)



'''
for pdf_file in pdf_files:

    if os.path.isfile(pdf_file):

        info = pdf2image.pdfinfo_from_path(pdf_file, userpw=None, poppler_path=None)

        maxPages = info["Pages"]

        page1 = pdf2image.convert_from_path(pdf_file,first_page=1,last_page=1)[0]
        if not end_vol:
            end_vol = maxPages

        # Assuming all images are the same size, get dimensions of first image
        w, h = page1.size
        N = int((end_vol - start_vol) / 2)

        # Create a numpy array of integers to store the average
        # arrRight = numpy.zeros((h, w), numpy.uint8)
        # arrLeft = numpy.zeros((h, w), numpy.uint8)
        arrRight = numpy.zeros((h, w, 3), numpy.float)
        arrLeft = numpy.zeros((h, w, 3), numpy.float)

        imarr = numpy.zeros((h, w, 3), numpy.float)

        for n in range(1, maxPages + 1, 50):
            chunk = pdf2image.convert_from_path(pdf_file, first_page=n, last_page=min(n + 50 - 1, maxPages))
            print("pdf converti")

            # Build up average pixel intensities, casting each image as an array of integers
            for i, page in enumerate(chunk):
                n_page = i+1
                if start_vol <= n_page <= end_vol:
                    # imarr = numpy.array(page.convert("L"), dtype=numpy.uint8)
                    imarr = numpy.array(page, dtype=numpy.float)
                    if n_page % 2 == 0:
                        arrLeft = arrLeft + imarr / N
                        print("pg")
                    else:
                        arrRight = arrRight + imarr / N
                        print("pd")

        # Round values in array and cast as 8-bit integer
        arrLeft = numpy.array(numpy.round(arrLeft), dtype=numpy.uint8)
        arrRight = numpy.array(numpy.round(arrRight), dtype=numpy.uint8)

        pdf_file_name = ".".join(pdf_file.split(".")[:-1])

        # Generate, save and preview final image
        # pil_cover4 = Image.fromarray(arrLeft, mode="L")
        pil_cover4 = Image.fromarray(arrLeft, mode="RGB")
        pil_cover4.save(pdf_file_name + "-cover4.png")

        # pil_cover1 = Image.fromarray(arrRight, mode="L")
        pil_cover1 = Image.fromarray(arrRight, mode="RGB")
        pil_cover1.save(pdf_file_name + "-cover1.png")
    else:
        print("pdf not found:")
        print(pdf_file)

'''

# covers_width = int((W*2+marges*2+spine) * ppi)
# covers_height = int((H+marges*2) * ppi)
# pil_covers = Image.new('L', (covers_width, covers_height), 0)
# pil_covers.paste(pil_cover4, (0,0))
# pil_covers.paste(pil_cover1, (int((6+spine) * ppi), 0))
#
# pil_covers.save("covers-"+str(start_vol)+"-"+str(end_vol)+".png")
