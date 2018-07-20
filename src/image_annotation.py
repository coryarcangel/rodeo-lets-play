import cv2
import numpy as np

def annotate_img(img, texts = [], rects = []):
    """ 
    Uses opencv drawing functions to add text and shapes to given image.
    Args:
        img: numpy array with original image
        texts: list of (x, y, text) tuples
        rects: list of (x, y, width, height, color) tuples
    Returns:
        numpy array with annotated image 
    """
    ann_img = img

    for x, y, width, height, color in rects:
        cv2.rectangle(ann_img, (x, y), (x + width, y + height), color, 3)

    for x, y, text in texts:
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (255, 255, 255)
        cv2.putText(ann_img, text, (x, y), font, 4, color, 2, cv2.LINE_AA)

    return ann_img