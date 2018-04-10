import os
import sys
import tensorflow as tf
from datetime import datetime

# Local Imports
from ai_estimator import QEstimator
from ai_state import AIStateProcessor

# Simple variables
start_time = datetime.now()
experiment_dir = os.path.abspath("./experiments/{}".format(start_time)) # Where we save our checkpoints and graphs

# Tensorflow setup
tf.reset_default_graph()
global_step = tf.Variable(0, name="global_step", trainable=False) # Create a global step variable

# Create estimators
q_estimator = QEstimator(scope="q", summaries_dir=experiment_dir)
target_estimator = QEstimator(scope="target_q")

# State processor
state_processor = AIStateProcessor()

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
