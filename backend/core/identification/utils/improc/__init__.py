import cv2 as cv
import os
import numpy as np
import json
# import easyocr
import math
import re

BASE_DIR = os.path.dirname(__file__)

# Возвращает сторону, в которую повёрнут контур
def get_side(contour):
    dots = []
    for i in contour:
        dots.append([i[0][0], i[0][1]])
    dots = sorted(dots, key=lambda x: x[0])
    if abs(dots[0][1] - dots[1][1]) < abs(dots[2][1] - dots[3][1]):
        return 'l'
    else:
        return 'r'


# Возвращает угол, на который повёрнут знак, и расстояние до него
def get_sign_position(ph_w, s_x, spp_w, sp_h, r_dim, side):
    fov = 40
    sp_w = sp_h * (r_dim['width'] / r_dim['height'])
    ph_t = abs(ph_w / 2 - s_x)
    if spp_w <= sp_w:
        angle = math.degrees(math.acos(spp_w / sp_w))
    else:
        angle = 0
    if side == 'r':
        angle = -angle
    false_dist = r_dim['width'] / (2 * math.tan(math.radians(fov / 2)))
    depth = false_dist * ph_w / sp_w
    trans = ph_t * r_dim['width'] / sp_w
    dist = math.sqrt(math.pow(depth, 2) + math.pow(trans, 2))
    return {'angle': round(angle, 2),
            'dist': round(dist, 2)}


# Возвращает список частей эталонов по цвету
def get_color_templates(color):
    templates_json_path = os.path.join(BASE_DIR, color, 'templates.json')
    if os.path.exists(templates_json_path):
        with open(templates_json_path) as f:
            templates = json.load(f)
        for template in templates:
            template['img'] = get_template(color, template['name'])
        return templates
    else:
        return []


# Возвращает часть эталона в оттенках серого
def get_template(color, name):
    image_path = os.path.join(BASE_DIR, color, 'templates', f'{name}.bmp')
    image = cv.imread(image_path)
    image = cv.GaussianBlur(image, (7, 7), 0)
    image = cv.medianBlur(image, 5)
    greyscale = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    return greyscale


# Возвращает отретушированное фото и его вариант в оттенках серого
def get_prepared_image(path):
    image = cv.imread(path)

    if image.shape[1] > 2000:
        percent = 2000 / image.shape[0]
        width = int(image.shape[1] * percent)
        height = int(image.shape[0] * percent)
        dim = (width, height)
        image = cv.resize(image, dim)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv.createCLAHE(clipLimit=3., tileGridSize=(5, 5))

    lab = cv.cvtColor(image, cv.COLOR_BGR2LAB)
    l, a, b = cv.split(lab)

    l2 = clahe.apply(l)

    lab = cv.merge((l2, a, b))
    image = cv.cvtColor(lab, cv.COLOR_LAB2BGR)

    # Применение размытий и приведение изображения в чб
    image = cv.GaussianBlur(image, (5, 5), 0)
    image = cv.medianBlur(image, 1)
    greyscale = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    return image, greyscale


# Сопоставляет части эталонов со знаками и добавляет
# к информации о знаках список голосов
def find_templates(templates, signs):
    for sign in signs:
        votes = {}
        img2 = cv.cvtColor(sign['img'], cv.COLOR_BGR2GRAY)
        for template in templates:
            result = cv.matchTemplate(img2, template['img'],
                                      cv.TM_CCORR_NORMED)
            min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
            for vote in template['votes']:
                if vote in votes:
                    votes[vote].append(max_val)
                else:
                    votes[vote] = [max_val]
        for vote in votes:
            votes[vote] = np.mean(votes[vote])
        sign['votes'] = votes
    return 0


# Возвращает объект со списками четырёхугольных контуров по цветам
def get_colored_contours(image):
    colors = [
        {'color': (0, 0, 255),
         'hsv_min': (0, 50, 20),
         'hsv_max': (10, 255, 255),
         'contours': [],
         'color_name': 'red'},
        {'color': (0, 255, 0),
         'hsv_min': (35, 50, 20),
         'hsv_max': (85, 255, 255),
         'contours': [],
         'color_name': 'green'}
    ]
    # Выборка контуров по цветам
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    for i in colors:
        if i['color_name'] == 'red':
            mask1 = cv.inRange(hsv, i['hsv_min'], i['hsv_max'])
            mask2 = cv.inRange(hsv, (160, 50, 20), (179, 255, 255))
            mask = cv.bitwise_or(mask1, mask2)
        else:
            mask = cv.inRange(hsv, i['hsv_min'], i['hsv_max'])
        kernel = np.ones((2, 2), np.uint8)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
        mask = cv.dilate(mask, kernel, iterations=1)
        mask = cv.erode(mask, kernel, iterations=1)
        contours, hierarchy = cv.findContours(mask,
                                              cv.RETR_TREE,
                                              cv.CHAIN_APPROX_NONE)
        for i2, cnt in enumerate(contours):
            area = cv.contourArea(cnt)
            if area > 1000 and hierarchy[0][i2][3] == -1:
                arclen = cv.arcLength(cnt, True)
                eps = 0.01
                epsilon = arclen * eps
                approx = cv.approxPolyDP(cnt, epsilon, True)
                if len(approx) == 4:
                    if cv.isContourConvex(approx):
                        i['contours'].append({'contour': approx,
                                              'side': get_side(approx)})
    return colors


# Общая функция, получаят путь к фото, возвращает набо знаков
def process_image(path):
    templates = {
        'red': [],
        'green': []
    }
    for key, value in templates.items():
        templates[key] = get_color_templates(key)

    img, img_g = get_prepared_image(path)

    colors = get_colored_contours(img)

    signs = {
        'red': [],
        'green': []
    }

    for color in colors:
        for cnt in color['contours']:
            x, y, w, h = cv.boundingRect(cnt['contour'])
            crop = img[y:(y + h), x:(x + w)]
            signs[color['color_name']].append({'img': cv.resize(crop,
                                                                (200,
                                                                 200)),
                                               'x': x,
                                               'y': y,
                                               'w': w,
                                               'h': h,
                                               'side': cnt['side']})

    for key, value in signs.items():
        if value:
            find_templates(templates[key], value)

    result = []
    for key, col_signs in signs.items():
        signs_json_path = os.path.join(BASE_DIR, key, 'signs.json')
        if os.path.exists(signs_json_path):
            with open(signs_json_path) as f:
                base_signs = json.load(f)
        for sign in col_signs:
            if sign['votes']:
                max_key = max(sign['votes'], key=sign['votes'].get)
                max_value = sign['votes'][max_key]
                if max_value > 0.9:
                    pos = get_sign_position(img.shape[1],
                                          sign['x'],
                                          sign['w'],
                                          sign['h'],
                                          base_signs[max_key],
                                          sign['side'])
                    pos['name'] = max_key
                    result.append(pos)
    return result
