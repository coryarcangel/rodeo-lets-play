""" Code to transform images from KK:Hollywood into numerical state """

import tensorflow as tf
from concurrent import futures
from darkflow.net.build import TFNet
from config import TFNET_CONFIG, CURRENT_IMG_CONFIG
from image_circles import get_image_circles, GALAXY8_VYSOR_HOUGH_CONFIG
from image_blob import BlobDetector
from image_contours import get_kim_action_color_shapes
from image_color import get_image_color_features
from image_ocr import ImageOCRProcessor
from ai_state_data import AIState

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
            state_futures = [
                executor.submit(get_pil_state),
                executor.submit(get_yolo_state),
                executor.submit(get_circles_state),
                # executor.submit(get_blobs),
                executor.submit(get_shapes),
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
