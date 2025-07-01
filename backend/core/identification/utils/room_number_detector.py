import cv2
import pytesseract
import numpy as np
import os
import re

def order_points(pts):
    # Упорядочить точки: [левый верх, правый верх, правый низ, левый низ]
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def preprocess_roi(roi):
    # Увеличиваем ROI
    scale = 3
    roi_big = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    # Otsu threshold
    _, otsu = cv2.threshold(roi_big, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Adaptive threshold
    adaptive = cv2.adaptiveThreshold(roi_big, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    return [roi_big, otsu, adaptive]

def try_ocr_on_roi(roi, patterns, ocr_configs):
    roi_variants = preprocess_roi(roi)
    roi_variants += [cv2.bitwise_not(r) for r in roi_variants]
    for roi_var in roi_variants:
        for config in ocr_configs:
            text = pytesseract.image_to_string(roi_var, config=config)
            text = text.strip().replace(" ", "")
            for pat in patterns:
                match = re.search(pat, text)
                if match:
                    number = match.group(0)
                    return number
    return None

def filter_and_sort_contours(contours, img_shape, min_w=40, min_h=20, max_ratio=8, min_ratio=1.5, max_roi=20):
    h_img, w_img = img_shape
    filtered = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < min_w or h < min_h:
            continue
        if w > w_img // 2 or h > h_img // 2:
            continue
        aspect = w / h if h != 0 else 0
        if not (min_ratio <= aspect <= max_ratio):
            continue
        filtered.append((cnt, w * h))
    # Оставляем только max_roi самых крупных
    filtered = sorted(filtered, key=lambda x: -x[1])[:max_roi]
    return [cnt for cnt, _ in filtered]

def find_room_numbers(image_path, debug_dir="debug_rois", max_results=3):
    """
    Находит номера кабинетов на табличках на двери.
    :param image_path: путь к изображению
    :param debug_dir: папка для сохранения ROI
    :return: список уникальных номеров
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Пробуем два варианта: с морфологией и без
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    images_for_contours = [thresh, morph]
    contour_labels = ["thresh", "morph"]

    results = []
    roi_count = 0
    patterns = [r"[A-Z][0-9]{3,}"]
    ocr_configs = [
        '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
        '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    ]
    max_roi = 20
    h_img, w_img = gray.shape

    # 1. Поиск по threshold и морфологии
    for img_idx, img in enumerate(images_for_contours):
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered_contours = filter_and_sort_contours(contours, (h_img, w_img))
        for cnt in filtered_contours:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.05 * peri, True)
            if len(approx) == 4:
                pts = approx.reshape(4, 2)
                warped = four_point_transform(gray, pts)
                roi = warped
            else:
                x, y, w, h = cv2.boundingRect(cnt)
                roi = gray[y:y+h, x:x+w]
            number = try_ocr_on_roi(roi, patterns, ocr_configs)
            if number:
                results.append(number)
                if len(results) >= max_results:
                    return results
    # 2. Поиск по Canny edge detection
    canny = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered_contours = filter_and_sort_contours(contours, (h_img, w_img))
    for cnt in filtered_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        roi = gray[y:y+h, x:x+w]
        number = try_ocr_on_roi(roi, patterns, ocr_configs)
        if number:
            results.append(number)
            if len(results) >= max_results:
                return results
    # 3. Если ничего не найдено — пробуем всю картинку и центральную область
    if len(results) < max_results:
        number = try_ocr_on_roi(gray, patterns, ocr_configs)
        if number:
            results.append(number)
    if len(results) < max_results:
        ch, cw = h_img // 2, w_img // 2
        cx, cy = w_img // 2, h_img // 2
        roi = gray[cy-ch//2:cy+ch//2, cx-cw//2:cx+cw//2]
        number = try_ocr_on_roi(roi, patterns, ocr_configs)
        if number:
            results.append(number)
    return results 