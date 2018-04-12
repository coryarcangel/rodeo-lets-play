import logging
import os
import sys
import time
import tensorflow as tf
from datetime import datetime

# Local Imports
from ai_estimator import QEstimator
from ai_state import AIStateProcessor
from device_client import get_default_device_client

# Config
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Simple variables
start_time = datetime.now()
experiment_dir = os.path.abspath("./experiments/{}".format(start_time)) # Where we save our checkpoints and graphs
logger = logging.getLogger('default')

# Tensorflow setup
tf.reset_default_graph()
global_step = tf.Variable(0, name="global_step", trainable=False) # Create a global step variable

# Create estimators
# q_estimator = QEstimator(scope="q", summaries_dir=experiment_dir)
# target_estimator = QEstimator(scope="target_q")

# State processor
state_processor = AIStateProcessor()

# Device Client
device_client = get_default_device_client()

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    device_client.start()

    # Loop
    frame = 0
    while True:
        logger.debug('Loop Frame #%d' % frame)
        filename = 'screen_%d.jpg' % frame
        device_client.send_screenshot_command(filename)

        # Analyze screenshot
        state = state_processor.process_from_file(sess, filename)
        logger.info('%s: %s' % (filename, state.to_text()))

        # Remove used file
        os.remove(filename)

        frame += 1
