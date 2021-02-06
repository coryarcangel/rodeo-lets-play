""" Code to transform images from KK:Hollywood into numerical state """

import tensorflow as tf
import cv2
from concurrent import futures
from darkflow.net.build import TFNet
from config import TFNET_CONFIG, CURRENT_IMG_CONFIG, HOUGH_CIRCLES_CONFIG
from image_circles import get_image_circles
from image_blob import BlobDetector
from image_contours import get_kim_action_color_shapes
from image_color import get_image_color_features
from image_ocr import ImageOCRProcessor
from ai_state_data import AIState
from util import convert_rect_between_rects


def _process_image_objects(image_objects, image_size, scale=1):
    '''
    Expects output from darkflow like {
        'label',
        'confidence',
        'topleft',
        'bottomright'
    }[]
    '''
    if not image_objects:
        return []

    def process_obj(obj):
        x = obj['topleft']['x']
        y = obj['topleft']['y']
        w = obj['bottomright']['x'] - x
        h = obj['bottomright']['y'] - y
        rect = (x, y, w, h)
        if scale != 1:
            scaled_image_rect = (0, 0, image_size[0] / scale, image_size[1] / scale)
            rect = convert_rect_between_rects(rect, (0, 0, image_size[0], image_size[1]), scaled_image_rect)

        return {
            'label': obj['label'],
            'confidence': float(obj['confidence']),
            'rect': rect
        }

    return [process_obj(i) for i in image_objects]


class AIStateProcessor(object):
    """ Top-level class for translating an image into state """

    def __init__(self, image_config):
        self.image_config = image_config
        self.ocr_processor = ImageOCRProcessor(image_config)
        self.tfnet = TFNet(TFNET_CONFIG)
        self.blob_detector = BlobDetector()

    def process_from_file(self, sess, filename):
        """
        Args:
            sess: A Tensorflow session object
            filename: A string filepath to a png image of KK:H gameplay
        Returns:
            A processed AIState object.
        """

        return AIState(**self.ocr_processor.process_filename(filename))

    def process_from_np_img(self, sess, np_img, scale=1):
        """
        Args:
            sess: A Tensorflow session object
            np_img: np array of image pixels
        Returns:
            A processed AIState object.

        FPS with sync pil and yolo: ~3.9
        FPS with threaded pil and yolo: ~6.8
        """

        scaled_np_img = np_img
        if scale != 1:
            height, width, _ = np_img.shape
            new_size = (int(width * scale), int(height * scale))
            scaled_np_img = cv2.resize(np_img, dsize=(new_size))

        np_img_3chan = np_img[:, :, :3]
        scaled_np_img_3chan = scaled_np_img[:, :, :3]
        scaled_height, scaled_width, _ = scaled_np_img_3chan.shape

        # Reads text via OCR, etc
        def get_pil_state():
            return self.ocr_processor.process_np_img(np_img)

        # Gets the very valuable yolo objects
        def get_yolo_state():
            yolo_result = self.tfnet.return_predict(scaled_np_img_3chan)
            return {'image_objects': _process_image_objects(yolo_result, image_size=(scaled_width, scaled_height), scale=scale)}

        # Gets Tappable circles!!
        def get_circles_state():
            circles = get_image_circles(np_img, HOUGH_CIRCLES_CONFIG)

            # Try to Filter out the menu circles
            tap_circles = circles

            return {'tap_circles': tap_circles}

        # Gets Blobs
        def get_blobs():
            blobs = self.blob_detector.get_image_blobs(np_img_3chan)
            return {'blobs': blobs}

        # Gets Contours
        def get_shapes():
            shapes = get_kim_action_color_shapes(np_img)
            return {'shapes': shapes}

        # Gets Color Features
        def get_color_features():
            color_features = get_image_color_features(np_img_3chan)
            return {'color_features': color_features}

        state_data = {}
        with futures.ThreadPoolExecutor() as executor:
            state_components = [
                ('pil_state', get_pil_state),
                ('yolo_state', get_yolo_state),
                ('circles_state', get_circles_state),
                # ('blobs_state', get_blobs),
                ('shapes_state', get_shapes),
                ('color_state', get_color_features)
            ]

            state_futures = [executor.submit(c[1]) for c in state_components]

            futures.wait(state_futures)
            for i in range(len(state_futures)):
                try:
                    future = state_futures[i]
                    data = future.result()
                    state_data.update(data)
                except Exception as e:
                    name = state_components[i][0]
                    print('Exception getting %s: %s' % (name, e))

        return AIState(**state_data)


def get_image_state(filename, image_config=CURRENT_IMG_CONFIG):
    """ Utility function to get state from a single image """
    processor = AIStateProcessor(image_config=image_config)

    with tf.Session() as sess:
        tf.global_variables_initializer().run()

        state = processor.process_from_file(sess, filename)
        return state
