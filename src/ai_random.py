"""Selects actions basically randomly based on predefined probabilities."""

import itertools
import numpy as np
import tensorflow as tf
import plotting
from kim_logs import get_kim_logger
from ai_actions import ActionGetter, ActionWeighter, Action


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
    stats = plotting.EpisodeStats(
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

        yield total_t, i_episode, plotting.EpisodeStats(
            episode_lengths=stats.episode_lengths[:i_episode + 1],
            episode_rewards=stats.episode_rewards[:i_episode + 1])
