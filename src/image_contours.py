''' Module inspired by https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/ '''
import cv2
import imutils
from concurrent import futures
from image_blob import get_center_color
from util import convert_point_between_rects, convert_rect_between_rects
from config import CONTOUR_PROCESS_HEIGHT, ACTION_SHAPE_COLOR_RANGES


def get_contour_shape(c):
    # approximate the contour
    try:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.01 * peri, True)
    except Exception as e:
        print(e)
        return None

    vert_names = {
        '3': 'triangle',
        '4': 'rectangle',
        '5': 'pentagon',
        '6': 'hexagon',
        '7': 'octagon',
        '8': 'octagon'
    }

    verts = len(approx)
    shape_name = vert_names[str(verts)] if str(verts) in vert_names else 'contour'
    return shape_name, verts


def get_contour_shape_data(c, image, resized_image):
    try:
        # Compute center and area
        M = cv2.moments(c)
        contour_area = M["m00"] if M["m00"] > 0 else 1
        x = int((M["m10"] / contour_area))
        y = int((M["m01"] / contour_area))
        bounding_rect = cv2.boundingRect(c)
        bounding_area = bounding_rect[2] * bounding_rect[3]

        image_rect = (0, 0, image.shape[0], image.shape[1])
        resized_rect = (0, 0, resized_image.shape[0], resized_image.shape[1])
        ratio = image.shape[0] / float(resized_image.shape[0])

        point = convert_point_between_rects((x, y), resized_rect, image_rect)

        rect = convert_rect_between_rects(bounding_rect, resized_rect, image_rect)
        area = rect[2] * rect[3]

        shape, verts = get_contour_shape(c)

        return {
            'shape': shape,
            'verts': verts,
            'point': point,
            'area': area,
            'boundsArea': bounding_area,
            'contourArea': contour_area,
            'areaRatio': float(bounding_area) / contour_area,
            'rect': rect,
            'rawRect': bounding_rect,
            'contour': (c.astype('float') * ratio).astype('int')  # mult by ratio
        }
    except Exception as e:
        print(e)
        return None


def get_grayscale_image_shapes(image):
    # Resize for performance
    img = imutils.resize(image, width=300)

    # Convert to grayscale, blur, threshold
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2)

    cv2.imshow('Threshold', img)
    cv2.waitKey(0)

    # find contours
    _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def get_shape(c):
        s = get_contour_shape_data(c, image, img)
        if s is not None:
            color, dom_color = get_center_color(image, s['point'])
            s['color'] = color
            s['dom_color'] = dom_color
        return s

    shapes = [get_shape(c) for c in contours]

    return [s for s in shapes if s and s['shape']]


def get_color_shape_data(shape_color_range, c, image, resized_image):
    data = get_contour_shape_data(c, image, resized_image)
    data['action_shape'] = shape_color_range.action_shape
    data['color_label'] = shape_color_range.color_label
    return data


def print_color_shapes(color_shapes):
    for s in color_shapes:
        print(s['action_shape'], s['color_label'], 'verts:', s['verts'], s['rawRect'], 'area:', s['boundsArea'], s['areaRatio'])


def get_image_colored_shapes(image, shape_color_ranges):
    '''
    Image is numpy image. shape_color_ranges is list of ShapeColorRange tuples

    We use contour detection to detect solid patches of color, which is how most
    selectable bubbles in the game are detected.
    '''

    TESTING = False
    SHOW_PRE_SHAPES = True
    if TESTING:
        shape_color_ranges = [s for s in shape_color_ranges if s.color_label in ('White')]

    # Resize for performance
    img = image
    img = imutils.resize(image, height=CONTOUR_PROCESS_HEIGHT, inter=cv2.INTER_LINEAR)

    # Blur to handle dumb pixel stuff
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # Convert to hsv
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    shapes = []

    def run_shape_range(item):
        # Mask image to only within given color range(s)
        mask = None
        for lower, upper in item.get_color_ranges():
            range_mask = cv2.inRange(hsv, lower, upper)
            if mask is None:
                mask = range_mask
            else:
                mask = cv2.addWeighted(mask, 1, range_mask, 1, 0)
        res = cv2.bitwise_and(img, img, mask=mask)
        if TESTING: cv2.imshow('Res', res); cv2.waitKey(0); cv2.destroyWindow('Res')

        # Convert to grayscale and threshold
        res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('Gray', res); cv2.waitKey(0)
        res = cv2.threshold(res, 100, 255, cv2.THRESH_BINARY)[1]
        # cv2.imshow('Threshold', res); cv2.waitKey(0)

        # Find contours (cv2 version independent)
        contour_res = cv2.findContours(res, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contour_res[1] if len(contour_res) == 3 else contour_res[0]

        # Get colored shapes
        color_shapes = [get_color_shape_data(item, c, image, img) for c in contours]

        # filter for at least reasonable shapes
        color_shapes = [cs for cs in color_shapes if cs['boundsArea'] > 60 and cs['contourArea'] > 10]

        # filter for this ShapeColorRange
        if TESTING and SHOW_PRE_SHAPES: print_color_shapes(color_shapes)
        color_shapes = [cs for cs in color_shapes if cs
                        and cs['boundsArea'] >= item.min_area
                        and cs['boundsArea'] <= item.max_area
                        and cs['verts'] >= item.min_verts
                        and cs['verts'] <= item.max_verts
                        and cs['areaRatio'] >= item.min_area_ratio
                        and cs['areaRatio'] <= item.max_area_ratio
                        and cs['rawRect'][1] >= item.min_y]
        if TESTING:
            print("Drawn Shapes:")
            print_color_shapes(color_shapes)
        return color_shapes

    THREADED = False
    if THREADED:
        with futures.ThreadPoolExecutor() as executor:
            shape_futures = [executor.submit(lambda: run_shape_range(x)) for x in shape_color_ranges]
            futures.wait(shape_futures)
            for item in shape_futures:
                try:
                    shapes += item.result()
                except Exception as e:
                    print('Exception running threaded shape: %s' % (e))
    else:
        for item in shape_color_ranges:
            shapes += run_shape_range(item)

    return shapes


def get_kim_action_color_shapes(image):
    shapes = get_image_colored_shapes(image, ACTION_SHAPE_COLOR_RANGES)
    return shapes


def draw_shapes(image, shapes):
    for shape in shapes:
        # cv2.drawContours(image, [shape['contour']], -1, (0, 255, 0), 2)
        x, y, w, h = shape['rect']
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(image, '%s %d' % (shape['shape'], shape['verts']), (x - 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 2)

    cv2.imshow('Shapes', imutils.resize(image, height=500))
    cv2.waitKey(0)
    cv2.destroyWindow('Shapes')


if __name__ == '__main__':
    sources = [
        'src/img/redtest.png',
        'src/img/speech_actions_ss_01.png',
        'src/img/gold_and_white_test.png',
        'src/img/henry_screenshots/red_x.png',
        'src/img/henry_screenshots/red_x_2.png',
        'src/img/henry_screenshots/yellow_and_white.png',
        'src/img/henry_screenshots/green_and_grey.png',
        'src/img/henry_screenshots/blue_and_red.png',
        'src/img/henry_screenshots/teal.png',
        'src/img/henry_screenshots/vysor_red_x.png',
        'src/img/henry_screenshots/vysor_red_x_2.png',
        'src/img/henry_screenshots/vysor_red_x_3.png',
        'src/img/henry_screenshots/vysor_green_grey.png',
        'src/img/henry_screenshots/vysor_silver.png',
        'src/img/henry_screenshots/vysor_teal.png',
        'src/img/henry_screenshots/vysor_white_yellow.png',
        'src/img/henry_screenshots/vysor_gold.png',
        'src/img/lightning_on_ground.png',
        'src/img/star_on_ground.png',
        'src/img/stars_money_people.png',
    ]
    for src in sources:
        image = cv2.imread(src)
        resized = imutils.resize(image, height=CONTOUR_PROCESS_HEIGHT, inter=cv2.INTER_LINEAR)
        print(src, image.shape, image.shape[0] / image.shape[1], resized.shape)
        # cv2.imshow(src, resized); cv2.waitKey(0); # cv2.destroyWindow('Res')
        shapes = get_kim_action_color_shapes(image)
        print("Drawn Shapes:")
        print_color_shapes(shapes)
        draw_shapes(image, shapes)
