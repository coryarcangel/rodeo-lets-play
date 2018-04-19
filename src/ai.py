"""Glues all of the modules together and runs the ai gamer on a device."""

import logging
import os
import sys
from datetime import datetime
import tensorflow as tf

# Local Imports
from ai_deep_q import deep_q_learning
from ai_random import random_learning
from ai_env import DeviceClientKimEnv, ScreenshotKimEnv
from ai_estimator import QEstimator
from device_client import get_default_device_client

# Config
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
RANDOM = True
STATIC_SCREENSHOT = True

def main():
    """
    Runs the ai infinitely.
    """

    # Simple variables
    start_time = datetime.now()
    experiment_dir = os.path.abspath("./experiments/{}".format(start_time)) # Where we save our checkpoints and graphs
    logger = logging.getLogger('default')

    # Tensorflow setup
    tf.reset_default_graph()
    global_step = tf.Variable(0, name="global_step", trainable=False) # Create a global step variable

    # Create estimators
    q_estimator = QEstimator(scope="q", summaries_dir=experiment_dir)
    target_estimator = QEstimator(scope="target_q")

    # Device Client and Env
    device_client = get_default_device_client() if not STATIC_SCREENSHOT else None
    env = DeviceClientKimEnv(client=device_client) if not STATIC_SCREENSHOT else ScreenshotKimEnv()

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        device_client.start()

        if RANDOM:
            for step, stats in random_learning(sess=sess, env=env):
                logger.info("\n%d Episode Reward: %s", step, stats.episode_rewards[-1])
        else:
            for step, stats in deep_q_learning(sess=sess,
                                               env=env,
                                               q_estimator=q_estimator,
                                               target_estimator=target_estimator,
                                               experiment_dir=experiment_dir,
                                               num_episodes=10000):
                logger.info("\n%d Episode Reward: %s", step, stats.episode_rewards[-1])


if __name__ == "__main__":
    main()
