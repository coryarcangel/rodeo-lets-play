""" Code to transform images from KK:Hollywood into numerical state """

import json
import logging
from collections import namedtuple
import numpy as np #pylint: disable=E0401
import tensorflow as tf #pylint: disable=E0401
import tesserocr #pylint: disable=E0401
from PIL import Image #pylint: disable=E0401
from darkflow.net.build import TFNet
from config import TFNET_CONFIG

# Image Configs
ImageConfig = namedtuple("ImageConfig", [
    "width",
    "height",
    "top_menu_height",
    "top_menu_padding",
    "top_menu_item_width",
    "money_item_left",
    "stars_item_left"
])

IMG_CONFIG_IPHONE7PLUS = ImageConfig(
    width=2208,
    height=1242,
    money_item_left=1170,
    stars_item_left=1568,
    top_menu_height=115,
    top_menu_padding=30,
    top_menu_item_width=240
)

IMG_CONFIG_STUDIOBLU = ImageConfig(
    width=1280,
    height=720,
    money_item_left=680,
    stars_item_left=884,
    top_menu_height=60,
    top_menu_padding=10,
    top_menu_item_width=120
)

IMG_CONFIG_GALAXY8 = ImageConfig(
    width=1280,
    height=720,
    money_item_left=680,
    stars_item_left=884,
    top_menu_height=60,
    top_menu_padding=10,
    top_menu_item_width=120
)

# Constants
OUTPUT_IMAGE_SIZE = [160, 80] # width x height
STATE_INPUT_SHAPE = [4]

class AIState(object):
    """
    Incorporates all known information about a frame of KK:H, including:
        * image -
        * money - number
        * stars - number
        * image_objects - list of {label: str, confience: num rect: (x,y,w,h)} objects
    """
    def __init__(self, image_shape, money=0, stars=0, image_objects=[]):
        self.image_shape = image_shape
        self.money = money
        self.stars = stars
        self.image = tf.placeholder(shape=image_shape, dtype=tf.uint8)
        self.image_objects = self._process_image_objects(image_objects)
        self.logger = logging.getLogger('AIState')

    @classmethod
    def deserialize(cls, data):
        return cls(**json.loads(data))

    def __str__(self):
        return 'Money: {} | Stars: {}'.format(self.money, self.stars)

    def _process_image_objects(self, image_objects):
        ''' Expects output from darkflow like {'label', 'confidence', 'topleft', 'bottomright'}[] '''
        def process_obj(obj):
            x = obj['topleft']['x']
            y = obj['topleft']['y']
            w = obj['bottomright']['x'] - x
            h = obj['bottomright']['y'] - y
            return {
                'label': obj['label'],
                'confidence': obj['confidence'],
                'rect': (x, y, w, h)
            }

        return map(image_objects, process_obj)

    def serialize(self):
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
        return np.array([1, 2, 3])

class AIGameplayImageProcessor(object):
    """
    Processes raw KK:H images into state.
    For now, resizes it and converts it to grayscale.
    In the future: use YOLO to translate image into object locations, and read known fixed-position HUD elements
    """
    def __init__(self, image_config):
        self.image_shape = [image_config.width, image_config.height, 3]
        self.output_image_size = OUTPUT_IMAGE_SIZE

        # Build the Tensorflow graph
        with tf.variable_scope("state_processor"):
            self.input_image = tf.placeholder(shape=self.image_shape, dtype=tf.uint8)

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
            self.output_image = tf.image.resize_images(self.output_image, self.output_image_size, method=resize_method)

            # Remove 1-dimensional components
            self.output_image = tf.squeeze(self.output_image)

    def process_image(self, sess, image):
        """
        Args:
            sess: A Tensorflow session object
            image: An image tensor with shape equal to `self.image_config.width and self.image_config.height`
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
        val = int(''.join(filter(str.isdigit, text.encode('ascii', 'ignore'))))
        return val
    except: #pylint: disable=W0702
        return 0

class AIStateProcessor(object):
    """ Top-level class for translating an image into state """
    def __init__(self, image_config=IMG_CONFIG_STUDIOBLU):
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
        # Get shape
        width, height = image.size
        image_shape = (width, height, 3)

        # get OCR text from known HUD elements
        money = self._read_hud_value(image, self.image_config.money_item_left)
        stars = self._read_hud_value(image, self.image_config.stars_item_left)

        return {
            'image_shape': image_shape,
            'money': money,
            'stars': stars
        }

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
        """

        # Get PIL stuff
        image = Image.fromarray(np_img).convert('RGB')
        state_data = self._get_pil_image_state_data(image)

        # Get YOLO stuff
        yolo_result = self.tfnet.return_predict(np_img)
        state_data['image_objects'] = yolo_result

        return AIState(**state_data)

def get_image_state(filename, image_config=IMG_CONFIG_GALAXY8):
    """ Utility function to get state from a single image """
    processor = AIStateProcessor(image_config=image_config)

    with tf.Session() as sess:
        tf.global_variables_initializer().run()

        state = processor.process_from_file(sess, filename)
        return state
