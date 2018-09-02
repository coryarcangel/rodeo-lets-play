""" Code to transform images from KK:Hollywood into numerical state """

import json
import logging
import numpy as np
import tensorflow as tf
import tesserocr
from concurrent import futures
from PIL import Image
from darkflow.net.build import TFNet
from config import TFNET_CONFIG, CURRENT_IMG_CONFIG

# Constants
OUTPUT_IMAGE_SIZE = [160, 80]  # width x height
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

    def __init__(self, image_shape=None,
                 money=0, stars=0, image_objects=None):
        self.image_shape = image_shape
        self.money = money
        self.stars = stars
        self.image = tf.placeholder(shape=image_shape, dtype=tf.uint8)
        self.image_objects = image_objects if image_objects is not None else []
        self.logger = logging.getLogger('AIState')

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


class AIGameplayImageProcessor(object):
    """
    Processes raw KK:H images into state.
    For now, resizes it and converts it to grayscale.
    In the future: use YOLO to translate image into object locations,
    and read known fixed-position HUD elements
    """

    def __init__(self, image_config):
        self.image_shape = [image_config.width, image_config.height, 3]
        self.output_image_size = OUTPUT_IMAGE_SIZE

        # Build the Tensorflow graph
        with tf.variable_scope("state_processor"):
            self.input_image = tf.placeholder(
                shape=self.image_shape, dtype=tf.uint8)

            # Convert to grayscale
            self.grayscale_image = tf.image.rgb_to_grayscale(self.input_image)

            # Crop to non-menu area
            image_width, image_height, _ = self.image_shape
            self.output_image = tf.image.crop_to_bounding_box(
                self.grayscale_image,
                image_config.top_menu_height,
                0,
                image_height - image_config.top_menu_height,
                image_width
            )

            # Resize for performance
            resize_method = tf.image.ResizeMethod.NEAREST_NEIGHBOR
            self.output_image = tf.image.resize_images(
                self.output_image, self.output_image_size, method=resize_method)

            # Remove 1-dimensional components
            self.output_image = tf.squeeze(self.output_image)

    def process_image(self, sess, image):
        """
        Args:
            sess: A Tensorflow session object
            image: An image tensor with shape equal to
            `[self.image_config.width, self.image_config.height]`
        Returns:
            Tuple of (output_image, grayscale_image)
        """
        # get processed image for gameplay area
        sess.run(self.output_image, {self.input_image: image})
        return self.output_image, self.grayscale_image


def read_num_from_img(image):
    """ Performs OCR on image and converts text to number """
    text = tesserocr.image_to_text(image).strip()
    try:
        f = filter(str.isdigit, text.encode('ascii', 'ignore').decode('utf-8'))
        t = ''.join(f)
        val = int(t)
        return val
    except BaseException:
        return 0


class AIStateProcessor(object):
    """ Top-level class for translating an image into state """

    def __init__(self, image_config):
        self.image_config = image_config
        self.tfnet = TFNet(TFNET_CONFIG)

    def _read_hud_value(self, image, left):
        padding = self.image_config.top_menu_padding
        height = self.image_config.top_menu_height
        width = self.image_config.top_menu_item_width
        item_crop_box = (left, padding, left + width, height - padding)
        hud_image = image.crop(item_crop_box)
        value = read_num_from_img(hud_image)
        return value

    def _get_pil_image_state_data(self, image):
        '''
            FPS with no text reading: ~7.5
            FPS with straight sync text reading: ~3.0
            FPS with thread pool text reading: ~3.9
        '''
        # Get shape
        width, height = image.size
        image_shape = (width, height, 3)

        # get OCR text from known HUD elements
        values = {'image_shape': image_shape}

        with futures.ThreadPoolExecutor() as executor:
            future_to_key = {
                executor.submit(self._read_hud_value, image, self.image_config.money_item_left): 'money',
                executor.submit(self._read_hud_value, image, self.image_config.stars_item_left): 'stars'
            }
            for future in futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    values[key] = future.result()
                except Exception as e:
                    print('Exception reading value: %s', e)

        return values

    def process_from_file(self, sess, filename):
        """
        Args:
            sess: A Tensorflow session object
            filename: A string filepath to a png image of KK:H gameplay
        Returns:
            A processed AIState object.
        """

        # Read image with pillow
        image = Image.open(filename).convert('RGB')
        pil_data = self._get_pil_image_state_data(image)

        return AIState(**pil_data)

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

        # Reads text via OCR, etc
        def get_pil_state():
            image = Image.fromarray(np_img).convert('RGB')
            return self._get_pil_image_state_data(image)

        # Gets the very valuable yolo objects
        def get_yolo_state():
            np_img_3chan = np_img[:, :, :3]
            yolo_result = self.tfnet.return_predict(np_img_3chan)
            return {'image_objects': _process_image_objects(yolo_result)}

        state_data = {}
        with futures.ThreadPoolExecutor() as executor:
            state_futures = [
                executor.submit(get_pil_state),
                executor.submit(get_yolo_state)
            ]

            for future in futures.as_completed(state_futures):
                try:
                    data = future.result()
                    state_data.update(data)
                except Exception as e:
                    print('Exception getting state: %s', e)

        return AIState(**state_data)


def get_image_state(filename, image_config=CURRENT_IMG_CONFIG):
    """ Utility function to get state from a single image """
    processor = AIStateProcessor(image_config=image_config)

    with tf.Session() as sess:
        tf.global_variables_initializer().run()

        state = processor.process_from_file(sess, filename)
        return state
