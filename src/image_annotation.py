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
    elif 'Blob' in label:
        return colors['purple']
    elif confidence is None:
        return colors['black']
    if confidence > 0.75:
        return colors['b']
    elif confidence > 0.5:
        return colors['darkorchid']
    elif confidence > 0.25:
        return colors['gold']
    else:
        return colors['white']


def draw_img_text(img, p=(0, 0), text='text',
                  font_scale=1, color=colors['white'], thickness=2,
                  font=cv2.FONT_HERSHEY_SIMPLEX):
    """
    Args:
        img: numpy array
        p: (x, y)
        text: string
        font: string
        color: (r, g, b) tuple
    Returns:
        numpy array with annotations
    """
    cv2.putText(img, text, p, font, font_scale, color, thickness, cv2.LINE_AA)
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


def draw_img_line(img, p1=(0, 0), p2=(100, 100), color=colors['white'], thickness=3):
    """
    Args:
        img: numpy array
        p1: (x, y) tuple
        p2: (x, y) tuple
        color: (r, g, b) tuple
        thickness: number
    Returns:
        numpy array with annotations
    """
    cv2.line(img, p1, p2, color, thickness)
    return img


def draw_img_crosshairs(img, p=(0, 0), color=colors['white'], thickness=2):
    """
    Args:
        img: numpy array
        p: (x, y) tuple
        color: (r, g, b) tuple
        thickness: number
    Returns:
        numpy array with annotations
    """
    x, y = p
    h, w, _ = img.shape
    r = 5
    draw_img_line(img, (w, y), (x + r, y), color, thickness)
    draw_img_line(img, (x, 0), (x, y - r), color, thickness)
    draw_img_line(img, (0, y), (x - r, y), color, thickness)
    draw_img_line(img, (x, h), (x, y + r), color, thickness)
    draw_img_rect(img, x - r, y - r, r * 2, r * 2, color, -1)
    return img


class AnnotatedImageStream(object):
    ''' This creates the affected screen capture, which is the visual output of
        the project '''

    def __init__(self, window_name='annotations'):
        self.window_name = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    def show_image(self, img, ai_state, recent_touch=None):
        """
        Shows the given opencv image with annotations from the AiState

        Args:
            img: numpy array
            ai_state: AiState object
            recent_touch: {'p', 'label', 'prob'} dict or None
        """
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
                ann_img, (x + w + 10, y + 10), text, 0.6, color)

        if recent_touch:
            r_point = recent_touch['p']
            r_color = (0, 0, 255)
            ann_img = draw_img_crosshairs(ann_img, r_point, r_color)
            if recent_touch['prob']:
                prob_text = '{}%'.format(round(recent_touch['prob'] * 100, 1))
                prob_point = (r_point[0] + 8, r_point[1] - 8)
                ann_img = draw_img_text(ann_img, prob_point, prob_text, 0.4, r_color, 1)

        # Draw Static Stuff!!
        # for a, args in ActionGetter.MenuTaps:
        #     x, y = [int(args[k]) for k in ['x', 'y']]
        #     ann_img = draw_img_rect(ann_img, x - 10, y - 10, 20, 20)

        cv2.imshow(self.window_name, ann_img)
        # wait 1 ms (no time) for a key press (required to run a lot of backend
        # cv2 image showing stuff?)
        cv2.waitKey(1)
