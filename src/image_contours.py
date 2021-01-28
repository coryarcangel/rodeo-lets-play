''' Module inspired by https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/ '''
import cv2
import imutils
from image_blob import get_center_color
from action_shape import action_shape_color_ranges

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
    shape_name = vert_names[str(verts)] if str(verts) in vert_names else 'circle'
    return shape_name, verts


def get_contour_shape_data(c, ratio):
    try:
        # Compute center and area
        M = cv2.moments(c)
        area = M["m00"] if M["m00"] > 0 else 1

        cX = int((M["m10"] / area) * ratio)
        cY = int((M["m01"] / area) * ratio)

        shape, verts = get_contour_shape(c)
        return {
            'shape': shape,
            'verts': verts,
            'point': (cX, cY),
            'area': area * ratio,
            'contour': (c.astype('float') * ratio).astype('int') # mult by ratio
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
    img = imutils.resize(image, width=300)
    ratio = image.shape[0] / float(img.shape[0])

    # Blur to handle dumb pixel stuff
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # Convert to hsv
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    shapes = []

    for label, lower, upper, min_area in color_ranges:
        # Mask image to only within given color range
        mask = cv2.inRange(hsv, lower, upper)
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
        color_shapes = [get_contour_shape_data(c, ratio) for c in contours]
        color_shapes = [cs for cs in color_shapes if cs and cs['area'] >= min_area]
        for cs in color_shapes:
            cs['color_label'] = label

        shapes += color_shapes

    return shapes


def get_kim_action_color_shapes(image):
    shapes = get_image_colored_shapes(image, action_shape_color_ranges)
    return shapes


def get_grayscale_image_shapes(image):
    # Resize for performance
    img = imutils.resize(image, width=300)
    ratio = image.shape[0] / float(img.shape[0])

    # Convert to grayscale, blur, threshold
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2)

    cv2.imshow('Threshold', img)
    cv2.waitKey(0)

    # find contours
    _, contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def get_shape(c):
        s = get_contour_shape_data(c, ratio)
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
    image = cv2.imread('src/img/speech_actions_ss_03.png')
    shapes = get_kim_action_color_shapes(image)
    print([(s['shape'], s['verts'], s['point'], s['area']) for s in shapes])

    draw_shapes(image, shapes)
