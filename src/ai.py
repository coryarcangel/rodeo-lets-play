"""Glues all of the modules together and runs the ai gamer on a device."""

import logging
import os
from datetime import datetime
import tensorflow as tf

# Local Imports
from config import configure_logging, CURRENT_PHONE_RECT, CURRENT_IMG_CONFIG
from ai_deep_q import deep_q_learning
from ai_random import random_learning
from ai_env import DeviceClientKimEnv, ScreenshotKimEnv
from ai_estimator import QEstimator
from device_client import DeviceClient

# Config
RANDOM = True
STATIC_SCREENSHOT = False
configure_logging()


def main():
    """
    Runs the ai infinitely.
    """

    # Simple variables
    start_time = datetime.now()
    # Where we save our checkpoints and graphs
    experiment_dir = os.path.abspath("./experiments/{}".format(start_time))
    logger = logging.getLogger('main')

    # Tensorflow setup
    tf.reset_default_graph()
    # Create a global step variable pylint: disable=W0612
    global_step = tf.Variable(0, name="global_step", trainable=False)

    # Create estimators
    q_estimator = QEstimator(
        scope="q",
        summaries_dir=experiment_dir) if not RANDOM else None
    target_estimator = QEstimator(scope="target_q") if not RANDOM else None

    # Device Client
    device_client = DeviceClient(
        CURRENT_PHONE_RECT,
        CURRENT_IMG_CONFIG) if not STATIC_SCREENSHOT else None
    device_client.start()

    # Env
    env = DeviceClientKimEnv(
        client=device_client) if not STATIC_SCREENSHOT else ScreenshotKimEnv()

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        learning_gen = None
        if RANDOM:
            learning_gen = random_learning(
                sess=sess, env=env, max_episode_length=1000)
        else:
            learning_gen = deep_q_learning(sess=sess,
                                           env=env,
                                           q_estimator=q_estimator,
                                           target_estimator=target_estimator,
                                           experiment_dir=experiment_dir,
                                           num_episodes=10000)

        for _, episode_idx, stats in learning_gen:
            logger.info("EPISODE #%d: Reward: %.0f, Steps: %d",
                        episode_idx,
                        stats.episode_rewards[-1],
                        stats.episode_lengths[-1])


if __name__ == "__main__":
    main()
