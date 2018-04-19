""" Code to transform images from KK:Hollywood into numerical state """

import logging
import numpy as np #pylint: disable=E0401
import tensorflow as tf #pylint: disable=E0401
import tesserocr #pylint: disable=E0401
from PIL import Image #pylint: disable=E0401

# Constants
IMAGE_CONFIG_IPHONE7PLUS = {
    'shape': [2208, 1242, 3],
    'money_width_mult': 0.53,
    'stars_width_mult': 0.71
}
OUTPUT_IMAGE_SIZE = [160, 80] # width x height
STATE_INPUT_SHAPE = [4]
HUD_MENU_HEIGHT = 115 # pixels
HUD_MENU_PADDING = 30 # pixels
HUD_MENU_ITEM_WIDTH = 240 # pixels

class AIState(object):
    """
    Incorporates all known information about a frame of KK:H, including:
        * image -
        * money - number
        * stars - number
        * tappable_objects - list of (x,y,w,h) tuples
    """
    def __init__(self, image_shape, money=0, stars=0):
        self.image_shape = image_shape
        self.money = money
        self.stars = stars
        self.image = tf.placeholder(shape=image_shape, dtype=tf.uint8)
        self.tappable_objects = []
        self.logger = logging.getLogger('AIState')

    def __str__(self):
        return 'Money: {} | Stars: {}'.format(self.money, self.stars)

    def get_reward(self):
        """ Returns total value of state """
        return self.money + self.stars

    def log(self):
        """ Logs string representation of state to INFO """
        self.logger.info(self)

    def to_input(self):
        """ Converts high-level object into numbers with shape STATE_INPUT_SHAPE """
        return np.array([1, 2, 3])

class AIGameplayImageProcessor():
    """
    Processes raw KK:H images into state.
    For now, resizes it and converts it to grayscale.
    In the future: use YOLO to translate image into object locations, and read known fixed-position HUD elements
    """
    def __init__(self, image_shape, output_image_size=OUTPUT_IMAGE_SIZE):
        self.image_shape = image_shape
        self.output_image_size = output_image_size

        # Build the Tensorflow graph
        with tf.variable_scope("state_processor"):
            self.input_image = tf.placeholder(shape=self.image_shape, dtype=tf.uint8)

            # Convert to grayscale
            self.grayscale_image = tf.image.rgb_to_grayscale(self.input_image)

            # Crop to non-menu area
            image_width, image_height, _ = self.image_shape
            self.output_image = tf.image.crop_to_bounding_box(
                self.grayscale_image,
                HUD_MENU_HEIGHT,
                0,
                image_height - HUD_MENU_HEIGHT,
                image_width
            )

            # Resize for performance
            resize_method = tf.image.ResizeMethod.NEAREST_NEIGHBOR
            self.output_image = tf.image.resize_images(self.output_image, self.output_image_size, method=resize_method)

            # Remove 1-dimensional components
            self.output_image = tf.squeeze(self.output_image)

    def process_image(self, sess, image):
        """
        Args:
            sess: A Tensorflow session object
            image: An image tensor with shape equal to `self.image_config['image_shape']`
        Returns:
            Tuple of (output_image, grayscale_image)
        """
        # get processed image for gameplay area
        sess.run(self.output_image, {self.input_image: image})
        return self.output_image, self.grayscale_image

class AIStateProcessor(object):
    def __init__(self, image_config=IMAGE_CONFIG_IPHONE7PLUS):
        self.image_config = image_config

    def _read_num_from_img(self, image):
        """ Performs OCR on image and converts text to number """
        text = tesserocr.image_to_text(image).strip()
        try:
            val = int(''.join(filter(str.isdigit, text.encode('ascii', 'ignore'))))
            return val
        except:
            return 0

    def _read_hud_value(self, image, left):
        item_crop_box = (left, HUD_MENU_PADDING, left + HUD_MENU_ITEM_WIDTH, HUD_MENU_HEIGHT - HUD_MENU_PADDING)
        hud_image = image.crop(item_crop_box)
        value = self._read_num_from_img(hud_image)
        return value

    def process_from_file(self, sess, filename):
        """
        Args:
            sess: A Tensorflow session object
            filename: A string filepath to a png image of KK:H gameplay
        Returns:
            A processed AIState object.
        """

        # Read image with pillow
        image = Image.open(filename)

        # Get shape
        width, height = image.size
        image_shape = (width, height, 3)

        # get OCR text from known HUD elements
        money = self._read_hud_value(image, self.image_config['money_width_mult'] * width)
        stars = self._read_hud_value(image, self.image_config['stars_width_mult'] * width)

        return AIState(image_shape=image_shape, money=money, stars=stars)

        # Decode image for tensorflow
        tf_image_file = tf.read_file(filename)
        tf_image = tf.image.decode_image(tf_image_file)

        # Process gameplay section with tensorflow
        gameplay_image_processor = AIGameplayImageProcessor(image_shape=image_shape)
        output_image, grayscale_image = gameplay_image_processor.process_image(sess, tf_image)


def get_image_state(filename):
    """ Utility function to get state from a single image """
    processor = AIStateProcessor()

    with tf.Session() as sess:
        tf.global_variables_initializer().run()

        state = processor.process_from_file(sess, filename)
        state.log()

        return state

if __name__ == "__main__":
    get_image_state('src/img/ios_screenshot_1.jpg')
