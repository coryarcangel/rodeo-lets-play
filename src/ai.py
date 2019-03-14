"""Glues all of the modules together and runs the ai gamer on a device."""

import logging
import os
from datetime import datetime
import tensorflow as tf

# Local Imports
from config import configure_logging, CURRENT_PHONE_RECT, VYSOR_CAP_AREA
from ai_deep_q import deep_q_learning
from ai_random import random_learning
from ai_heuristic import heuristic_learning
from ai_env import DeviceClientKimEnv, ScreenshotKimEnv
from ai_estimator import QEstimator
from device_client import DeviceClient

class LearningMode(object):
    """Enum-like iteration of all available learning methods """
    RANDOM = 0
    HEURISTIC = 1
    DEEP_Q = 2

# Config
learning_mode = LearningMode.Heuristic
STATIC_SCREENSHOT = False
configure_logging()


def main():
    """
    Runs the ai infinitely.
    """

    is_deep_q = learning_mode == LearningMode.DEEP_Q

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
        summaries_dir=experiment_dir) if is_deep_q else None
    target_estimator = QEstimator(scope="target_q") if is_deep_q else None

    # Device Client
    device_client = DeviceClient(
        CURRENT_PHONE_RECT,
        VYSOR_CAP_AREA) if not STATIC_SCREENSHOT else None
    device_client.start()

    # Env
    env = DeviceClientKimEnv(
        client=device_client) if not STATIC_SCREENSHOT else ScreenshotKimEnv()

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        # Create Learning Generator
        learning_gen = None
        if learning_mode == LearningMode.Random:
            learning_gen = random_learning(sess=sess, env=env, max_episode_length=1000)
        elif learning_mode == LearningMode.Heuristic:
            learning_gen = heuristic_learning(sess=sess, env=env, max_episode_length=1000)
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
