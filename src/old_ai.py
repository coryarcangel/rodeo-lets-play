"""Glues all of the modules together and runs the ai gamer on a device."""

import tensorflow as tf
import itertools
import numpy as np
from collections import namedtuple

# Local Imports
from kim_logs import get_kim_logger
from old_ai_env import DeviceClientKimEnv, ScreenshotKimEnv
from device_client import DeviceClient
from ai_actions import ActionGetter, ActionWeighter, Action
from heuristic_selector import HeuristicActionSelector


class LearningMode(object):
    """Enum-like iteration of all available learning methods """
    RANDOM = 0
    HEURISTIC = 1


# Config
learning_mode = LearningMode.HEURISTIC
STATIC_SCREENSHOT = False


EpisodeStats = namedtuple("Stats", ["episode_lengths", "episode_rewards"])


class RandomActionSelector(object):
    ''' Selects action from AIState randomly, with weighting based on projected
    value of types of moves '''

    def __init__(self):
        self.action_weighter = ActionWeighter()

    def select_state_action(self, state):
        # Get possible actions
        actions = ActionGetter.get_actions_from_state(state)

        # Choose randomly
        return self.action_weighter.select_action(actions, self.action_weighter.get_action_weight)


def random_learning(sess, env, num_episodes=100, max_episode_length=100000):
    """
    Args:
        sess: Tensorflow Session object
        env: AiEnv environment
        num_episodes: Number of episodes to run for
    Returns:
        An EpisodeStats object with two numpy arrays for episode_lengths and episode_rewards.
    """

    logger = get_kim_logger('random_learning')

    # Keeps track of useful statistics
    stats = EpisodeStats(
        episode_lengths=np.zeros(num_episodes),
        episode_rewards=np.zeros(num_episodes))

    total_t = sess.run(tf.train.get_global_step())

    selector = RandomActionSelector()

    for i_episode in range(num_episodes):
        # Reset the environment
        state = env.reset()

        # One step in the environment
        for step in itertools.count():
            # Print out which step we're on, useful for debugging.
            logger.info("Step %d (%d) @ Episode %d/%d, state: %s",
                        step, total_t, i_episode + 1, num_episodes, state)

            # Choose action randomly
            action, args = selector.select_state_action(state)

            # Take a step
            next_state, reward, done, _ = env.step(action, args)

            # Update statistics
            stats.episode_rewards[i_episode] = reward
            stats.episode_lengths[i_episode] = step

            if done or (max_episode_length > 0 and step >= max_episode_length):
                break

            state = next_state
            total_t += 1

        # Add summaries to tensorboard
        episode_summary = tf.Summary()
        episode_summary.value.add(
            simple_value=stats.episode_rewards[i_episode],
            node_name="episode_reward",
            tag="episode_reward")
        episode_summary.value.add(
            simple_value=stats.episode_lengths[i_episode],
            node_name="episode_length",
            tag="episode_length")

        yield total_t, i_episode, EpisodeStats(
            episode_lengths=stats.episode_lengths[:i_episode + 1],
            episode_rewards=stats.episode_rewards[:i_episode + 1])


def heuristic_learning(sess, env, num_episodes=1000, max_episode_length=100000):
    """
    Args:
        sess: Tensorflow Session object
        env: AiEnv environment
        num_episodes: Number of episodes to run for
    Returns:
        An EpisodeStats object with two numpy arrays for episode_lengths and episode_rewards.
    """

    logger = get_kim_logger('heuristic_learning')

    # Keeps track of useful statistics
    stats = EpisodeStats(
        episode_lengths=np.zeros(num_episodes),
        episode_rewards=np.zeros(num_episodes))

    total_t = sess.run(tf.train.get_global_step())

    for i_episode in range(num_episodes):
        # Reset the environment
        state = env.reset()

        selector = HeuristicActionSelector()

        # One step in the environment
        for step in itertools.count():
            # Print out which step we're on, useful for debugging.
            logger.info("Step %d (%d) @ Episode %d/%d, state: %s",
                        step, total_t, i_episode + 1, num_episodes, state)

            # Choose action
            action, args = selector.select_state_action(state)
            if action == Action.RESET:
                break

            # Get status
            status = selector.get_state_status(state)

            # Take a step
            next_state, reward, done, _ = env.step(action, args)

            # Update statistics
            stats.episode_rewards[i_episode] = reward
            stats.episode_lengths[i_episode] = step

            # Publish status
            env.action_state_manager.publish_data('ai-status-updates', status)

            if done or (max_episode_length > 0 and step >= max_episode_length):
                break

            state = next_state
            total_t += 1

        # Add summaries to tensorboard
        episode_summary = tf.Summary()
        episode_summary.value.add(
            simple_value=stats.episode_rewards[i_episode],
            node_name="episode_reward",
            tag="episode_reward")
        episode_summary.value.add(
            simple_value=stats.episode_lengths[i_episode],
            node_name="episode_length",
            tag="episode_length")

        yield total_t, i_episode, EpisodeStats(
            episode_lengths=stats.episode_lengths[:i_episode + 1],
            episode_rewards=stats.episode_rewards[:i_episode + 1])


def main():
    """
    Runs the old random or heuristic ai controllers infinitely.
    """

    # Simple variables
    logger = get_kim_logger('main')

    # Tensorflow setup
    tf.reset_default_graph()
    global_step = tf.Variable(0, name="global_step", trainable=False)

    # Device Client
    device_client = DeviceClient() if not STATIC_SCREENSHOT else None
    device_client.start()

    # Env
    env = DeviceClientKimEnv(
        client=device_client) if not STATIC_SCREENSHOT else ScreenshotKimEnv()

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

        # Create Learning Generator
        learning_gen = None
        if learning_mode == LearningMode.RANDOM:
            learning_gen = random_learning(sess=sess, env=env, max_episode_length=0)
        elif learning_mode == LearningMode.HEURISTIC:
            learning_gen = heuristic_learning(sess=sess, env=env, max_episode_length=0)

        for _, episode_idx, stats in learning_gen:
            logger.info("EPISODE #%d: Reward: %.0f, Steps: %d",
                        episode_idx,
                        stats.episode_rewards[-1],
                        stats.episode_lengths[-1])


if __name__ == "__main__":
    main()
