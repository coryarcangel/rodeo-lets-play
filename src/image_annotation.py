import cv2
import numpy as np
from matplotlib import colors as mcolors


def hex2rgb(hex):
    c = mcolors.to_rgb(hex)
    return tuple([int(255 * n) for n in c])


# https://matplotlib.org/examples/color/named_colors.html
colors = {
    name: hex2rgb(hex) for name,
    hex in dict(
        mcolors.BASE_COLORS,
        **mcolors.CSS4_COLORS).items()}

label_colors_map = {
    'person': colors['tomato'],
    'clock': colors['springgreen'],
    'tvmonitor': colors['black'],
    'laptop': colors['black'],
    'traffic light': colors['chartreuse'],
}


def get_img_object_color(label, confidence):
    if label in label_colors_map:
        return label_colors_map[label]
    elif 'Circle' in label:
        return colors['orange']
    if confidence > 0.75:
        return colors['b']
    elif confidence > 0.5:
        return colors['darkorchid']
    elif confidence > 0.25:
        return colors['gold']
    else:
        return colors['white']


def draw_img_text(img, x=0, y=0, text='text',
                  font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1,
                  color=colors['white']):
    """
    Args:
        img: numpy array
        x: number
        y: number
        text: string
        font: string
        color: (r, g, b) tuple
    Returns:
        numpy array with annotations
    """
    cv2.putText(img, text, (x, y), font, font_scale, color, 2, cv2.LINE_AA)
    return img


def draw_img_rect(img, x=0, y=0, w=100, h=100,
                  color=colors['white'], thickness=3):
    """
    Args:
        img: numpy array
        x: number
        y: number
        w: number
        h: number
        color: (r, g, b) tuple
        thickness: number
    Returns:
        numpy array with annotations
    """
    cv2.rectangle(img, (x, y), (x + w, y + h), color, thickness)
    return img


class AnnotatedImageStream(object):
    def __init__(self, window_name='annotations'):
        self.window_name = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    def show_image(self, img, ai_state):
        """ Shows the given opencv image with annotations from the AiState """
        # Nice docs here:
        # https://docs.opencv.org/3.1.0/d7/dfc/group__highgui.html#ga453d42fe4cb60e5723281a89973ee563

        ann_img = img
        for obj in ai_state.image_objects:
            label, confidence, rect = [obj[k]
                                       for k in ('label', 'confidence', 'rect')]

            color = get_img_object_color(label, confidence)

            x, y, w, h = rect
            ann_img = draw_img_rect(ann_img, x, y, w, h, color=color)

            text = '%s (%.2f)' % (label, confidence) if confidence else label
            ann_img = draw_img_text(
                ann_img, x + w + 10, y + 10, text, font_scale=0.6, color=color)

        # Draw Static Stuff!!
        # for a, args in ActionGetter.MenuTaps:
        #     x, y = [int(args[k]) for k in ['x', 'y']]
        #     ann_img = draw_img_rect(ann_img, x - 10, y - 10, 20, 20)

        cv2.imshow(self.window_name, ann_img)
        # wait 1 ms (no time) for a key press (required to run a lot of backend
        # cv2 image showing stuff?)
        cv2.waitKey(1)
