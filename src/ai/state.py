import tensorflow as tf

RawImageShape = [320, 640, 3]
StateInputShape = [4]

class AIState():
    """
    Incorporates all known information about a frame of KK:H, including:
        * image -
        * money - number
        * stars - number
        * tappable_objects - list of (x,y,w,h) tuples
    """
    def __init__(self):
        self.image = tf.placeholder(shape=RawImageShape, dtype=tf.uint8)
        self.money = 0
        self.stars = 0
        self.tappable_objects = []

    def to_input(self):
        """
        Converts high-level object into numbers with shape StateInputShape
        """
        return []

class AIStateProcessor():
    """
    Processes raw KK:H images into state.
    For now, resizes it and converts it to grayscale.
    In the future: use YOLO to translate image into object locations, and read known fixed-position HUD elements
    """
    def __init__(self):
        # Build the Tensorflow graph
        with tf.variable_scope("state_processor"):
            self.input_state = tf.placeholder(shape=RawImageShape, dtype=tf.uint8)
            self.output = tf.image.rgb_to_grayscale(self.input_state)
            self.output = tf.image.crop_to_bounding_box(self.output, 34, 0, 160, 160)
            self.output = tf.image.resize_images(
                self.output, [84, 84], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
            self.output = tf.squeeze(self.output)

    def process(self, sess, state):
        """
        Args:
            sess: A Tensorflow session object
            state: A [210, 160, 3] Atari RGB State
        Returns:
            A processed AIState object.
        """
        return sess.run(self.output, { self.input_state: state })
