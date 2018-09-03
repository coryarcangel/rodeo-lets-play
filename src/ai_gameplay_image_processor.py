'''
For now this module is totally unused, and is part of something
more deep-q style unsupervised learning approach
'''
import tensorflow as tf

OUTPUT_IMAGE_SIZE = [160, 80]  # width x height


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
        return self.output_image, self.grayscale_image
        sess.run(self.output_image, {self.input_image: image})
