''' Module inspired by https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/ '''
import cv2
import numpy as np


def get_image_circles(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # find circles
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        0.25,  # dp (inverse ratio of accumulator resolution)
        100,  # min distance between circles
        np.array([]),  # stupid circles param for C
        500,  # param1 (confusing)
        50,  # param2 (smaller means more false circles)
        20,  # min radius
        40)  # max radius

    return np.round(circles[0, :]).astype('int') if circles is not None else None


def draw_circles(image, circles):
    for x, y, r in circles:
        cv2.circle(image, (x, y), r, (0, 255, 0), 4)
        cv2.rectangle(image, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)

    cv2.imshow('Circles', cv2.resize(image, (960, 540)))
    cv2.waitKey(0)


if __name__ == '__main__':
    image = cv2.imread('src/img/galaxy8_screenshot_1.png')
    circles = get_image_circles(image)
    draw_circles(image, circles)
