""" Code to transform images from KK:Hollywood into numerical state """

import json
import logging
import numpy as np
import tensorflow as tf
from concurrent import futures
from darkflow.net.build import TFNet
from config import TFNET_CONFIG, CURRENT_IMG_CONFIG
from image_circles import get_image_circles, GALAXY8_VYSOR_HOUGH_CONFIG
from image_blob import BlobDetector
from image_color import get_image_color_features
from image_ocr import ImageOCRProcessor

# Constants
STATE_INPUT_SHAPE = [4]


def _process_image_objects(image_objects):
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
        return {
            'label': obj['label'],
            'confidence': float(obj['confidence']),
            'rect': (x, y, w, h)
        }

    return [process_obj(i) for i in image_objects]


class AIState(object):
    """
    Incorporates all known information about a frame of KK:H, including:
        * image -
        * money - number
        * stars - number
        * image_objects - list of {
            label: str,
            confidence: num,
            rect: (x,y,w,h)
          } objects
    """

    def __init__(self,
                 image_shape=None,
                 money=0,
                 stars=0,
                 image_objects=None,
                 tap_circles=[],
                 color_features=None,
                 blobs=[]):
        self.logger = logging.getLogger('AIState')
        self.image_shape = image_shape
        self.money = money
        self.stars = stars
        self.image = tf.placeholder(shape=image_shape, dtype=tf.uint8)
        self.color_features = color_features
        self.color_sig = color_features['color_sig'] if color_features is not None else 'none'
        self.image_objects = image_objects if image_objects is not None else []

        for idx, c in enumerate(tap_circles):
            x, y, r = c
            self.image_objects.append({
                'label': 'Circle #%d' % (idx + 1),
                'object_type': 'circle',
                'confidence': None,
                'rect': (x - r, y - r, 2 * r, 2 * r)
            })

        for idx, b in enumerate(blobs):
            x, y = b['point']
            r = int(b['size'] / 2.0)
            # TODO: can make object type stronger based on color / size of blob
            self.image_objects.append({
                'label': 'Blob #%d - %s' % (idx + 1, b['dom_color']),
                'object_type': 'blob',
                'confidence': None,
                'dom_color': b['dom_color'],
                'size': b['size'],
                'rect': (x - r, y - r, 2 * r, 2 * r)
            })

    @classmethod
    def deserialize(cls, data):
        ''' loads AIState from serialized json '''
        return cls(**json.loads(data))

    def __str__(self):
        return 'Money: {} | Stars: {}'.format(self.money, self.stars)

    def serialize(self):
        ''' serializes AIState into json '''
        return json.dumps({
            'money': self.money,
            'stars': self.stars,
            'image_objects': self.image_objects
        })

    def get_reward(self):
        """ Returns total value of state """
        return self.money + self.stars

    def log(self):
        """ Logs string representation of state to INFO """
        self.logger.info(self)

    def to_input(self):
        """ Converts high-level object into numbers with shape STATE_INPUT_SHAPE """
        return np.array([1, self.money, self.stars])


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

        # Decode image for tensorflow
        # tf_image_file = tf.read_file(filename)
        # tf_image = tf.image.decode_image(tf_image_file)
        #
        # # Process gameplay section with tensorflow
        # gameplay_image_processor = AIGameplayImageProcessor(image_config=self.image_config)
        # output_image, grayscale_image = gameplay_image_processor.process_image(sess, tf_image)

    def process_from_np_img(self, sess, np_img):
        """
        Args:
            sess: A Tensorflow session object
            np_img: np array of image pixels
        Returns:
            A processed AIState object.

        FPS with sync pil and yolo: ~3.9
        FPS with threaded pil and yolo: ~6.8
        """

        np_img_3chan = np_img[:, :, :3]

        # Reads text via OCR, etc
        def get_pil_state():
            return self.ocr_processor.process_np_img(np_img)

        # Gets the very valuable yolo objects
        def get_yolo_state():
            yolo_result = self.tfnet.return_predict(np_img_3chan)
            return {'image_objects': _process_image_objects(yolo_result)}

        # Gets Tappable circles!!
        def get_circles_state():
            circles = get_image_circles(np_img, GALAXY8_VYSOR_HOUGH_CONFIG)

            # Try to Filter out the menu circles
            tap_circles = [c for c in circles if c[1] < 350]

            return {'tap_circles': tap_circles}

        # Gets Blobs
        def get_blobs():
            blobs = self.blob_detector.get_image_blobs(np_img_3chan)
            return {'blobs': blobs}

        # Gets Color Features
        def get_color_features():
            color_features = get_image_color_features(np_img_3chan)

            return {'color_features': color_features}

        state_data = {}
        with futures.ThreadPoolExecutor() as executor:
            state_futures = [
                executor.submit(get_pil_state),
                executor.submit(get_yolo_state),
                executor.submit(get_circles_state),
                executor.submit(get_blobs),
                executor.submit(get_color_features)
            ]

            for future in futures.as_completed(state_futures):
                try:
                    data = future.result()
                    state_data.update(data)
                except Exception as e:
                    print('Exception getting state: %s' % e)

        return AIState(**state_data)


def get_image_state(filename, image_config=CURRENT_IMG_CONFIG):
    """ Utility function to get state from a single image """
    processor = AIStateProcessor(image_config=image_config)

    with tf.Session() as sess:
        tf.global_variables_initializer().run()

        state = processor.process_from_file(sess, filename)
        return state
