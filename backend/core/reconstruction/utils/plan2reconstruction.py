import cv2
import numpy as np
import trimesh
from shapely.geometry import Polygon
import logging
import os
from datetime import datetime
from shapely.ops import unary_union
import traceback
from PIL import Image

# --- Public API Functions ---

def reconstruct_3d_from_plan(image_path, user_mask_path):
    """
    The main pipeline function that replicates the successful logic from plan2_3d.py.
    It takes an image and a user-edited mask and returns a 3D mesh.
    """
    user_mask = cv2.imread(user_mask_path, cv2.IMREAD_GRAYSCALE)
    if user_mask is None:
        raise FileNotFoundError(f"User mask not found at {user_mask_path}")

    # Step 1: Get the automatic wall mask
    auto_mask = get_wall_mask(image_path)
    final_mask = auto_mask.copy()

    # Step 2: Apply user's additions (white areas)
    roi = (user_mask > 200).astype(np.uint8)
    if np.any(roi):
        img = load_image(image_path)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, roi_bin = cv2.threshold(img_gray, 120, 255, cv2.THRESH_BINARY_INV)
        roi_bin = cv2.bitwise_and(roi_bin, roi * 255)
        
        kernel = np.ones((7, 7), np.uint8) 
        roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_CLOSE, kernel)
        roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_OPEN, kernel)
        
        final_mask = cv2.bitwise_or(final_mask, roi_bin)

    # Step 3: Apply user's deletions (black areas)
    final_mask[user_mask < 50] = 0

    # Step 4: Find Hough lines on the final processed mask
    lines = cv2.HoughLinesP(final_mask, 1, np.pi/180, threshold=80, minLineLength=40, maxLineGap=10)
    
    # Step 5: Build 3D model from these lines
    mesh = lines_to_3d(lines, wall_thickness=10, wall_height=100)
    
    return mesh

def get_initial_mask_and_image(image_path):
    """Gets the initial mask for the editor and the original image."""
    img = load_image(image_path)
    auto_mask = get_wall_mask(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return auto_mask, img_rgb

def save_mesh(mesh, filename):
    """Saves the trimesh object to a file."""
    if mesh is not None:
        mesh.export(filename)
    else:
        raise ValueError('Nothing to save!')

def process_and_get_hough_preview(image_path, user_mask_path):
    """
    Processes image and user mask, finds Hough lines, and returns a preview image and the line data.
    """
    user_mask = cv2.imread(user_mask_path, cv2.IMREAD_GRAYSCALE)
    if user_mask is None:
        raise FileNotFoundError(f"User mask not found at {user_mask_path}")

    auto_mask = get_wall_mask(image_path)
    final_mask = auto_mask.copy()

    roi = (user_mask > 200).astype(np.uint8)
    if np.any(roi):
        img = load_image(image_path)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, roi_bin = cv2.threshold(img_gray, 120, 255, cv2.THRESH_BINARY_INV)
        roi_bin = cv2.bitwise_and(roi_bin, roi * 255)
        
        kernel = np.ones((7, 7), np.uint8) 
        roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_CLOSE, kernel)
        roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_OPEN, kernel)
        
        final_mask = cv2.bitwise_or(final_mask, roi_bin)

    final_mask[user_mask < 50] = 0

    lines = cv2.HoughLinesP(final_mask, 1, np.pi/180, threshold=80, minLineLength=40, maxLineGap=10)
    
    preview_image = cv2.cvtColor(final_mask, cv2.COLOR_GRAY2BGR)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(preview_image, (x1, y1), (x2, y2), (0, 0, 255), 3) # Draw red lines
            
    return preview_image, lines

# --- Internal "private" functions ---

def load_image(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f'Image not found: {path}')
    return img

def _binarize(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    mask = (s < 60) & (v < 80)
    binary = np.zeros_like(v)
    binary[mask] = 255
    return binary

def _morph(binary):
    kernel = np.ones((9, 9), np.uint8)
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
    return morph

def get_wall_mask(image_path):
    img = load_image(image_path)
    binary = _binarize(img)
    return _morph(binary)

def lines_to_3d(lines, wall_thickness=10, wall_height=100, add_floor=True, floor_thickness=5, wall_texture_path=None, floor_texture_path=None, texture_scale=150.0):
    """
    Converts lines from Hough transform to a 3D mesh.
    Includes robust checks for empty or invalid geometry.
    """
    if lines is None or len(lines) == 0:
        print("Warning: lines_to_3d received no lines to process.")
        return None 

    wall_meshes = []
    all_pts = []
    
    for line_arr in lines:
        if line_arr is None or len(line_arr) == 0:
            continue
        x1, y1, x2, y2 = line_arr[0]
        
        dx, dy = x2 - x1, y2 - y1
        length = np.hypot(dx, dy)
        if length < 1e-6: 
            continue
            
        nx, ny = -dy / length, dx / length
        
        half_thick = wall_thickness / 2
        p1 = (x1 + nx * half_thick, y1 + ny * half_thick)
        p2 = (x1 - nx * half_thick, y1 - ny * half_thick)
        p3 = (x2 - nx * half_thick, y2 - ny * half_thick)
        p4 = (x2 + nx * half_thick, y2 + ny * half_thick)
        
        poly = Polygon([p1, p2, p3, p4])
        if not poly.is_valid or poly.area < 1e-6: 
            continue
            
        all_pts.extend([p1, p2, p3, p4])
        
        try:
            mesh = trimesh.creation.extrude_polygon(poly, wall_height)
            wall_meshes.append(mesh)
        except Exception as e:
            print(f"Could not extrude polygon: {poly}. Error: {e}")
            continue

    if not wall_meshes:
        print("Warning: No valid meshes could be created from the lines.")
        return None 

    scene = trimesh.Scene()

    # Объединяем стены и накладываем текстуру
    if wall_meshes:
        wall_mesh = trimesh.util.concatenate(wall_meshes)
        if wall_texture_path and os.path.exists(wall_texture_path):
            try:
                # Создаем UV координаты для стен (простое наложение)
                uv = wall_mesh.vertices[:, :2] / texture_scale
                wall_mesh.visual = trimesh.visual.TextureVisuals(uv=uv, image=Image.open(wall_texture_path))
            except Exception as e:
                print(f"Could not apply wall texture: {e}")
        scene.add_geometry(wall_mesh)


    # Создаем пол и накладываем текстуру
    if add_floor and all_pts:
        try:
            all_pts_arr = np.array(all_pts)
            min_x, min_y = np.min(all_pts_arr, axis=0)
            max_x, max_y = np.max(all_pts_arr, axis=0)
            
            floor_poly = Polygon([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])
            if floor_poly.is_valid and floor_poly.area > 1e-6:
                floor_mesh = trimesh.creation.extrude_polygon(floor_poly, floor_thickness)
                floor_mesh.apply_translation([0, 0, -floor_thickness])
                
                if floor_texture_path and os.path.exists(floor_texture_path):
                    try:
                        # UV для пола
                        uv = floor_mesh.vertices[:, :2] / texture_scale
                        floor_mesh.visual = trimesh.visual.TextureVisuals(uv=uv, image=Image.open(floor_texture_path))
                    except Exception as e:
                        print(f"Could not apply floor texture: {e}")

                scene.add_geometry(floor_mesh)
        except Exception as e:
            print(f"Could not create floor. Error: {e}")

    return scene if not scene.is_empty else None

def find_walls(morph):
    contours, _ = cv2.findContours(morph, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def find_straight_walls(binary):
    lines = cv2.HoughLinesP(binary, 1, np.pi/180, threshold=80, minLineLength=40, maxLineGap=10)
    wall_img = np.zeros_like(binary)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(wall_img, (x1, y1), (x2, y2), 255, 5)
    return wall_img

def contours_to_3d(contours, height=100, floor_thickness=5):
    meshes = []
    all_pts = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if len(cnt) < 3 or area < 300:
            continue
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        pts = approx[:,0,:]
        all_pts.append(pts)
        poly = Polygon(pts)
        if not poly.is_valid or poly.area == 0:
            continue
        try:
            mesh = trimesh.creation.extrude_polygon(poly, height)
            meshes.append(mesh)
        except Exception:
            continue
    if all_pts:
        all_pts = np.vstack(all_pts)
        minx, miny = np.min(all_pts, axis=0)
        maxx, maxy = np.max(all_pts, axis=0)
        floor_poly = Polygon([
            (minx, miny),
            (maxx, miny),
            (maxx, maxy),
            (minx, maxy)
        ])
        floor_mesh = trimesh.creation.extrude_polygon(floor_poly, floor_thickness)
        meshes.append(floor_mesh)
    if meshes:
        return trimesh.util.concatenate(meshes)
    else:
        return None

def get_hough_lines_image(final_mask, hough_params=None):
    """
    Возвращает изображение с линиями Хафа, наложенными на маску.
    hough_params: dict с параметрами HoughLinesP (threshold, minLineLength, maxLineGap, thickness)
    """
    params = dict(threshold=80, minLineLength=40, maxLineGap=10, thickness=3)
    if hough_params:
        params.update(hough_params)
    lines = cv2.HoughLinesP(final_mask, 1, np.pi/180, threshold=params['threshold'],
                            minLineLength=params['minLineLength'], maxLineGap=params['maxLineGap'])
    color_img = cv2.cvtColor(final_mask, cv2.COLOR_GRAY2BGR)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(color_img, (x1, y1), (x2, y2), (0,0,255), params['thickness'])
    return color_img, lines 

def process_user_mask_pipeline(image_path, user_mask_path):
    """
    Полный pipeline: объединяет авто-маску и пользовательскую, морфология, Hough.
    Возвращает: (hough_lines_img, lines, final_mask)
    """
    auto_mask = get_wall_mask(image_path)
    user_mask = cv2.imread(user_mask_path, cv2.IMREAD_GRAYSCALE)
    final_mask = auto_mask.copy()
    roi = (user_mask > 200).astype(np.uint8)
    if np.any(roi):
        img = load_image(image_path)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, roi_bin = cv2.threshold(img_gray, 120, 255, cv2.THRESH_BINARY_INV)
        roi_bin = cv2.bitwise_and(roi_bin, roi*255)
        kernel = np.ones((7, 7), np.uint8)
        roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_CLOSE, kernel)
        roi_bin = cv2.morphologyEx(roi_bin, cv2.MORPH_OPEN, kernel)
        final_mask = cv2.bitwise_or(final_mask, roi_bin)
    final_mask[user_mask < 50] = 0
    kernel = np.ones((11, 11), np.uint8)
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)
    _, final_mask_bin = cv2.threshold(final_mask, 127, 255, cv2.THRESH_BINARY)
    # --- Поиск линий Хафа ---
    lines = cv2.HoughLinesP(final_mask_bin, 1, np.pi/180, threshold=80, minLineLength=40, maxLineGap=10)
    hough_lines = np.zeros_like(final_mask_bin)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(hough_lines, (x1, y1), (x2, y2), 255, 3)
    return hough_lines, lines, final_mask_bin 
