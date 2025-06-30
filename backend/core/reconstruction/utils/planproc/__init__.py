import cv2 as cv
import os
import numpy as np
import json
# import easyocr
import imutils
import re
import pywavefront
import itertools

BASE_DIR = os.path.dirname(__file__)

# Возвращает список знаков по цвету
def get_color_templates(color, size):
    signs_json_path = os.path.join(BASE_DIR, color, 'signs.json')
    if os.path.exists(signs_json_path):
        with open(signs_json_path) as f:
            signs = json.load(f)
    for key, sign in signs.items():
        sign['img'] = get_template(color, key, size)
    return signs


# Возвращает эталон в оттенках серого
def get_template(color, name, size):
    image_path = os.path.join(BASE_DIR, color, 'signs', f'{name}.bmp')
    image = cv.imread(image_path)
    image = cv.GaussianBlur(image, (3, 3), 0)
    image = cv.medianBlur(image, 1)

    percent = size / image.shape[0]
    width = int(image.shape[1] * percent)
    height = int(image.shape[0] * percent)
    dim = (width, height)
    image = cv.resize(image, dim)

    greyscale = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    return greyscale


# Возвращает отретушированное фото и его вариант в оттенках серого
def get_prepared_image(path):
    image = cv.imread(path)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv.createCLAHE(clipLimit=3., tileGridSize=(5, 5))

    lab = cv.cvtColor(image, cv.COLOR_BGR2LAB)
    l, a, b = cv.split(lab)

    l2 = clahe.apply(l)

    lab = cv.merge((l2, a, b))
    image = cv.cvtColor(lab, cv.COLOR_LAB2BGR)

    # Применение размытий и приведение изображения в чб
    image = cv.GaussianBlur(image, (3, 3), 0)
    image = cv.medianBlur(image, 1)
    greyscale = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    return image, greyscale


def clean_zeros(loc):
    new_loc = [[], []]
    for i, val in enumerate(loc[0]):
        if val != 0:
            new_loc[0].append(val)
            new_loc[1].append(loc[1][i])
    return new_loc


# Сопоставляет части эталонов со знаками
def find_signs(templates, image, image_og, color):
    signs = []
    threshold = 0
    width, height = image.shape[::-1]
    if color == 'red':
        threshold = 0.868
    else:
        threshold = 0.89
    for key, template in templates.items():
        name = key
        for i in range(-120, 120, 10):
            w, h = template['img'].shape[::-1]
            rotated = imutils.rotate_bound(template['img'], i)
            result = cv.matchTemplate(image, rotated,
                                      cv.TM_CCORR_NORMED)
            loc = np.where(result >= threshold)
            min_val = 0
            prev = 0
            for i, val in enumerate(loc[0]):
                if val > 0 and val <= (min_val + w) and val >= prev:
                    prev = val
                    loc[0][i] = 0
                    loc[1][i] = 0
                else:
                    prev = 0
                    min_val = val

            loc = clean_zeros(loc)
            for pt in zip(*loc[::-1]):
                # cv.putText(image_og, name, (pt[0] + w // 2, pt[1] + h // 2),
                #            cv.FONT_HERSHEY_COMPLEX, .7, (255, 0, 0), 2)
                # Удалить область
                cv.rectangle(image, (pt[0] + 10, pt[1] + 10), (pt[0] + w - 10, pt[1] + h - 10), (0, 0, 0), -1)
                signs.append({"name": name, "x": pt[0] + w // 2, "y": height - (pt[1] + h // 2)})
    return signs


def get_red_mask(image, gray):
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    mask1 = cv.inRange(hsv, (0, 50, 20), (10, 255, 255))
    mask2 = cv.inRange(hsv, (160, 50, 20), (179, 255, 255))
    mask = cv.bitwise_or(mask1, mask2)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv.erode(mask, kernel, iterations=1)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)

    contours, hierarchy = cv.findContours(mask,
                                          cv.RETR_TREE,
                                          cv.CHAIN_APPROX_NONE)
    black = np.zeros(image.shape[:2], dtype="uint8")
    exp_size = 10000
    for i, cnt in enumerate(contours):
        area = cv.contourArea(cnt)
        if area > 1000 and hierarchy[0][i][3] == -1:
            arclen = cv.arcLength(cnt, True)
            eps = 0.015
            epsilon = arclen * eps
            approx = cv.approxPolyDP(cnt, epsilon, True)
            if len(approx) == 4:
                x, y, w, h = cv.boundingRect(cnt)
                if h < exp_size:
                    exp_size = h
                cv.drawContours(black, [approx], -1, (255, 255, 255), -1)

    masked_image = cv.bitwise_and(gray, gray, mask=black)
    return masked_image, exp_size


def get_green_mask(image, gray):
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, (35, 50, 20), (85, 255, 255))
    kernel = np.ones((3, 3), np.uint8)
    mask = cv.erode(mask, kernel, iterations=1)
    kernel = np.ones((60, 60), np.uint8)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)
    masked_image = cv.bitwise_and(gray, gray, mask=mask)
    return masked_image


# ОНО ИЗВЛЕКАЕТ ИЗ ИЗОБРАЖЕНИЯ НОМЕРА И ЕЩЁ "ЗАМАЗЫВАЕТ" ИХ (не применяется)
# def clear_text(path):
#     result = []
#     img, img_g = get_prepared_image(path)

#     ret, th = cv.threshold(img_g, 0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
#     cv.namedWindow('thre', cv.WINDOW_NORMAL)

#     reader = easyocr.Reader(['en'], gpu=False)
#     numbers = reader.readtext(th, rotation_info=[90, 180, 270])
#     pattern = r'\d\d\d[a-z]?'
#     for n in numbers:
#         bbox, text, score = n
#         if type(bbox[0][0]) is not np.float64:
#             cv.rectangle(img, bbox[0], bbox[2], (200, 200, 200), -1)
#             if score > 0.5:
#                 match = re.match(pattern, text)
#                 if match:
#                     result.append({
#                                     "text": match.group(),
#                                     "x": bbox[0][0],
#                                     "y": bbox[0][1]
#                                 })

#     cv.imshow('thre', img)

#     cv.waitKey(0)

#     cv.destroyAllWindows()
#     return result


# ПОПЫТКА ПРИВЯЗКИ ЗНАКОВ К СТЕНАМ
def bind_signs(signs, model_path):
    scene = pywavefront.Wavefront(model_path, collect_faces=True)

    vertices = scene.vertices

    faces = scene.mesh_list[0].faces

    plan_signs = []

    for key, colors in signs.items():
        for sign in colors:
            dot1 = [sign["x"], sign["y"]]
            closest_i = -1
            closest_d = 100000000
            for i, face in enumerate(faces):
                dot2 = [vertices[face[0]][0], vertices[face[0]][1]]
                d = np.sqrt(np.square(dot1[0] - dot2[0]) + np.square(dot1[1] - dot2[1]))
                if d < closest_d:
                    closest_d = d
                    closest_i = i
            # Должен быть перпендикуляр КАК?
            a = [vertices[faces[closest_i][0]][0], vertices[faces[closest_i][0]][1]]
            b = dot1
            c = [a[0] + closest_d, a[1]]

            abac = (a[0] - b[0]) * (c[0] - b[0]) + (a[1] - b[1]) * (c[1] - b[1])
            ab = np.sqrt(np.square(a[0] - b[0]) + np.square(a[1] - b[1]))
            ac = np.sqrt(np.square(a[0] - c[0]) + np.square(a[1] - c[1]))

            cos = abac / (ab * ac)
            if cos >= 1:
                cos = -(cos % 1)
            angle = np.degrees(np.arccos(cos))
            if a[1] > dot1[1]:
                angle = 360 - angle
            angle = (angle // 45) * 45
            plan_signs.append({"name": sign["name"],
                               "x": a[0],
                               "y": a[1],
                               "angle": angle})

    return plan_signs


# Идентификация, принимает знаки с плана и с фото (вывод двух финальных функций), возвращает координаты метки пользователя
def get_user_pos(signs_plan, signs_photo, scale):
    cat_signs = []
    un_signs = []

    for sph in signs_photo:
        match_signs = []
        for spl in signs_plan:
            if sph["name"] == spl["name"]:
                spl["angle"] += sph["angle"]
                spl["dist"] = sph["dist"]
                match_signs.append(spl)
        if match_signs:
            if len(match_signs) == 1:
                un_signs.append(match_signs[0]["name"])
            cat_signs.append(match_signs)

    if len(cat_signs) == 1 and len(cat_signs[0]) == 1:
        sign = cat_signs[0][0]
        if sign["name"] in un_signs:
            x = sign["x"] + sign["dist"] * scale * np.cos(np.radians(sign["angle"]))
            y = sign["y"] + sign["dist"] * scale * np.sin(np.radians(sign["angle"]))

            return {"x": x, "y": y, "angle": 0}
        else:
            return "Знаков слишком мало/Нет уникальных знаков"
    else:
        combs = itertools.product(*cat_signs)

        min_c = -1
        min_d = 100000000

        for i, comb in enumerate(combs):
            dots = []
            for sign in comb:
                dots.append([int(sign["x"]), int(sign["y"])])
            dots = np.array(dots)
            if cv.arcLength(dots, True) <= min_d:
                min_d = cv.arcLength(dots, True)
                min_c = comb

        xs = []
        ys = []

        for sign in min_c:
            x_s = sign["x"] + sign["dist"] * scale * np.cos(np.radians(sign["angle"]))
            print(np.cos(np.radians(sign["angle"])))
            xs.append(x_s)
            y_s = sign["y"] + sign["dist"] * scale * np.sin(np.radians(sign["angle"]))
            print(np.sin(np.radians(sign["angle"])))
            ys.append(y_s)

        x = np.mean(xs)
        y = np.mean(ys)

        return {"x": x, "y": y, "angle": 0}


# Тоже финалка, получает путь к фото плана, привязывает знаки к модели, возвращает набор знаков
def process_image(plan_file_path, model_path):
    plan_img, plan_img_g = get_prepared_image(plan_file_path)

    red_mask, exp_size = get_red_mask(plan_img, plan_img_g)
    green_mask = get_green_mask(plan_img, plan_img_g)

    templates = {
        'red': [],
        'green': []
    }
    for key, value in templates.items():
        templates[key] = get_color_templates(key, exp_size)

    signs = {
        'red': [],
        'green': []
    }

    drawyimg = cv.cvtColor(plan_img_g, cv.COLOR_GRAY2BGR)

    signs['red'] = find_signs(templates['red'], red_mask, drawyimg, 'red')
    signs['green'] = find_signs(templates['green'], green_mask, drawyimg, 'green')
    # print(signs)
    signs_plan = bind_signs(signs, model_path)

    return signs_plan
