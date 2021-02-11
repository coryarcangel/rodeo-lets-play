''' Module inspired by https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/ '''
import cv2
import imutils
import time
from image_blob import get_center_color
from util import convert_point_between_rects
from config import CONTOUR_PROCESS_WIDTH, ACTION_SHAPE_COLOR_RANGES


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
        area = M["m00"] if M["m00"] > 0 else 1

        x = int((M["m10"] / area))
        y = int((M["m01"] / area))

        image_rect = (0, 0, image.shape[0], image.shape[1])
        resized_rect = (0, 0, resized_image.shape[0], resized_image.shape[1])
        ratio = image.shape[0] / float(resized_image.shape[0])

        point = convert_point_between_rects((x, y), resized_rect, image_rect)

        shape, verts = get_contour_shape(c)
        return {
            'shape': shape,
            'verts': verts,
            'point': point,
            'area': area * ratio * ratio,
            'rawArea': area,
            'contour': (c.astype('float') * ratio).astype('int')  # mult by ratio
        }
    except Exception as e:
        print(e)
        return None


def get_image_colored_shapes(image, color_ranges):
    '''
    Image is numpy image. color_ranges is list of tupes of
    (label, lower, upper, min_area) where lower and upper are hsv tuples
    '''

    # Resize for performance
    img = image
    img = imutils.resize(image, width=CONTOUR_PROCESS_WIDTH)

    # Blur to handle dumb pixel stuff
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # Convert to hsv
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    shapes = []

    for item in color_ranges:
        label = item.label
        # Mask image to only within given color range
        mask = cv2.inRange(hsv, item.lower, item.upper)
        res = cv2.bitwise_and(img, img, mask=mask)
        # cv2.imshow('Res', res); cv2.waitKey(0)

        # Convert to grayscale and threshold
        res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('Gray', res); cv2.waitKey(0)
        res = cv2.threshold(res, 100, 255, cv2.THRESH_BINARY)[1]
        # cv2.imshow('Threshold', res); cv2.waitKey(0)

        # Find contours (cv2 version independent)
        contour_res = cv2.findContours(res, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contour_res[1] if len(contour_res) == 3 else contour_res[0]

        # Get colored shapes
        color_shapes = [get_contour_shape_data(c, image, img) for c in contours]
        # for s in color_shapes: print('raw', label, s['verts'], s['rawArea'])
        color_shapes = [cs for cs in color_shapes if cs and
            cs['rawArea'] >= item.min_area and
            cs['rawArea'] <= item.max_area and
            cs['verts'] >= item.min_verts and
            cs['verts'] <= item.max_verts]
        # for s in color_shapes: print(label, s['verts'], s['rawArea'], s['point'])
        for cs in color_shapes:
            cs['color_label'] = label

        shapes += color_shapes

    return shapes


def get_kim_action_color_shapes(image):
    shapes = get_image_colored_shapes(image, ACTION_SHAPE_COLOR_RANGES)
    return shapes


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


def draw_shapes(image, shapes):
    for shape in shapes:
        cv2.drawContours(image, [shape['contour']], -1, (0, 255, 0), 2)
        cv2.putText(image, shape['shape'], shape['point'], cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 2)

    cv2.imshow('Shapes', image)
    cv2.waitKey(0)


if __name__ == '__main__':
    image = cv2.imread('src/img/redtest.png')
    shapes = get_kim_action_color_shapes(image)
    print([(s['shape'], s['verts'], s['point'], s['area']) for s in shapes])

    draw_shapes(image, shapes)
