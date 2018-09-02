import cv2
from ai_actions import ActionGetter

# TODO: might want to do annotation with matplotlib
# (https://matplotlib.org/api/_as_gen/matplotlib.patches.Rectangle.html)

WHITE = (255, 255, 255)


def draw_img_text(img, x=0, y=0, text='text',
                  font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1,
                  color=WHITE):
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
    cv2.putText(img, text, (x, y), font, font_scale, color, 1, cv2.LINE_AA)
    return img


def draw_img_rect(img, x=0, y=0, w=100, h=100, color=WHITE, thickness=3):
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
            x, y, w, h = rect
            ann_img = draw_img_rect(ann_img, x, y, w, h)

            text = '%s (%.2f)' % (label, confidence)
            ann_img = draw_img_text(
                ann_img, x + w + 10, y + 10, text, font_scale=0.6)

        # Draw Static Stuff!!
        # for a, args in ActionGetter.MenuTaps:
        #     x, y = [int(args[k]) for k in ['x', 'y']]
        #     ann_img = draw_img_rect(ann_img, x - 10, y - 10, 20, 20)

        cv2.imshow(self.window_name, ann_img)
        # wait 1 ms (no time) for a key press (required to run a lot of backend
        # cv2 image showing stuff?)
        cv2.waitKey(1)
