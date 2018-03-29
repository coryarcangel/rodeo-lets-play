import tensorflow as tf
import tesserocr
from PIL import Image

# Constants
Iphone7PlusRawImageShape = [2208, 1242, 3]
OutputImageSize = [160, 80] # width x height
StateInputShape = [4]
HudMenuHeight = 115 # pixels
HudMenuPadding = 30 # pixels
HudItemWidth = 240 # pixels

class AIState():
    """
    Incorporates all known information about a frame of KK:H, including:
        * image -
        * money - number
        * stars - number
        * tappable_objects - list of (x,y,w,h) tuples
    """
    def __init__(self, money=0, stars=0):
        self.image = tf.placeholder(shape=Iphone7PlusRawImageShape, dtype=tf.uint8)
        self.money = money
        self.stars = stars
        self.tappable_objects = []

    def read_image_scores(self):
        pass

    def log(self):
        print('Money: {} | Stars: {}'.format(self.money, self.stars))

    def to_input(self):
        """
        Converts high-level object into numbers with shape StateInputShape
        """
        return []

class AIGameplayImageProcessor():
    """
    Processes raw KK:H images into state.
    For now, resizes it and converts it to grayscale.
    In the future: use YOLO to translate image into object locations, and read known fixed-position HUD elements
    """
    def __init__(self, image_shape=Iphone7PlusRawImageShape, output_image_size=OutputImageSize):
        self.image_shape = image_shape
        self.output_image_size = output_image_size

        # Build the Tensorflow graph
        with tf.variable_scope("state_processor"):
            self.input_image = tf.placeholder(shape=self.image_shape, dtype=tf.uint8)

            # Convert to grayscale
            self.grayscale_image = tf.image.rgb_to_grayscale(self.input_image)

            # Crop to non-menu area
            image_width, image_height, _ = self.image_shape
            self.output_image = tf.image.crop_to_bounding_box(self.grayscale_image, HudMenuHeight, 0, image_height - HudMenuHeight, image_width)

            # Resize for performance
            resize_method = tf.image.ResizeMethod.NEAREST_NEIGHBOR
            self.output_image = tf.image.resize_images(self.output_image, self.output_image_size, method=resize_method)

            # Remove 1-dimensional components
            self.output_image = tf.squeeze(self.output_image)

    def process_image(self, sess, image):
        """
        Args:
            sess: A Tensorflow session object
            image: An image tensor with shape equal to `self.image_shape`
        Returns:
            Tuple of (output_image, grayscale_image)
        """
        # get processed image for gameplay area
        sess.run(self.output_image, { self.input_image: image })
        return self.output_image, self.grayscale_image

class AIStateProcessor():
    def read_num_from_img(self, image):
        """ Performs OCR on image and converts text to number """
        text = tesserocr.image_to_text(image).strip()
        try:
            val = int(''.join(filter(str.isdigit, text)))
            return val
        except:
            return 0

    def read_hud_value(self, image, left):
        item_crop_box = (left, HudMenuPadding, left + HudItemWidth, HudMenuHeight - HudMenuPadding)
        hud_image = image.crop(item_crop_box)
        value = self.read_num_from_img(hud_image)
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
        money = self.read_hud_value(image, 0.53 * width)
        stars = self.read_hud_value(image, 0.71 * width)
        return AIState(money=money, stars=stars)

        # Decode image for tensorflow
        tf_image_file = tf.read_file(filename)
        tf_image = tf.image.decode_image(tf_image_file)

        # Process gameplay section with tensorflow
        gameplay_image_processor = AIGameplayImageProcessor(image_shape=image_shape)
        output_image, grayscale_image = gameplay_image_processor.process_image(sess, tf_image)


def get_image_state(filename):
    processor = AIStateProcessor()

    with tf.Session() as sess:
        tf.global_variables_initializer().run()

        state = processor.process_from_file(sess, filename)
        state.log()

        return state

get_image_state('src/img/ios_screenshot_1.jpg')
