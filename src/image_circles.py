''' Module inspired by https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/ '''
import cv2
import numpy as np

GALAXY8_FULL_HOUGH_CONFIG = {
    'dp': 0.25,  # (inverse ratio of accumulator resolution)
    'minDist': 100,  # min distance between circles
    'param1': 500,  # (confusing)
    'param2': 50,  # (smaller means more false circles)
    'minRadius': 20,
    'maxRadius': 40
}

GALAXY8_VYSOR_HOUGH_CONFIG = {
    'dp': 0.25,  # (inverse ratio of accumulator resolution)
    'minDist': 30,  # min distance between circles
    'param1': 500,  # (confusing)
    'param2': 50,  # (smaller means more false circles)
    'minRadius': 5,
    'maxRadius': 20
}


def get_image_circles(image, hough_config=GALAXY8_VYSOR_HOUGH_CONFIG):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # find circles
    circles = cv2.HoughCircles(
        gray,
        method=cv2.HOUGH_GRADIENT,
        circles=np.array([]),  # stupid circles param for C
        **hough_config)

    if circles is None or len(circles) == 0:
        return []

    int_circles = np.round(circles[0, :]).astype('int')

    return [(int(x), int(y), int(r))
            for x, y, r in int_circles]  # leave numpy world


def draw_circles(image, circles):
    for x, y, r in circles:
        cv2.circle(image, (x, y), r, (0, 255, 0), 4)
        cv2.rectangle(image, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)

    cv2.imshow('Circles', cv2.resize(image, (960, 540)))
    cv2.waitKey(0)


if __name__ == '__main__':
    image = cv2.imread('src/img/galaxy8_screenshot_1.png')
    circles = get_image_circles(image, GALAXY8_FULL_HOUGH_CONFIG)
    draw_circles(image, circles)
