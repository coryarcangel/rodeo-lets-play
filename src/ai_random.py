"""Implements the "Deep Q Learning" algorithm"""

import itertools
import logging
import numpy as np
import tensorflow as tf
import plotting
from ai_actions import ActionGetter, Action


class RandomActionSelector(object):
    ''' Selects action from AIState randomly, with weighting based on projected
    value of types of moves '''

    def __init__(self):
        self.cur_state_id = ''

        self.ActionWeights = {
            Action.PASS: 25,
            Action.SWIPE_LEFT: 50,
            Action.SWIPE_RIGHT: 50,
            Action.TAP_LOCATION: 100
        }
        self.TapTypeWeights = {
            'menu': 1,
            'object': 100
        }
        self.TapObjectTypeWeights = {
            'frisbee': 500,
            'circle': 500,
            'clock': 500,
            'sports ball': 500,
            'traffic light': 10,
            'doorbell': 250,
            'person': 5,
            'umbrella': 5,
            'chair': 5
        }

    def get_action_weight(self, a_tup):
        ''' Assigns a weight to action based on its type / content '''
        action, args = a_tup
        action_type = args['type'] if 'type' in args else None
        object_type = args['object_type'].lower() if 'object_type' in args else None
        if action == Action.TAP_LOCATION and action_type in self.TapTypeWeights:
            if object_type and object_type in self.TapObjectTypeWeights:
                return self.TapObjectTypeWeights[object_type]
            return self.TapTypeWeights[action_type]
        if action in self.ActionWeights:
            return self.ActionWeights[action]
        return 1

    def select_state_action(self, state):
        # Get possible actions
        actions = ActionGetter.get_actions_from_state(state)

        # TODO: Change weights based on if state.color_sig is the same as the previous state's color sig

        # Assign weighted probabilities
        action_weights = [self.get_action_weight(a) for a in actions]
        total_weight = float(sum(action_weights))
        action_probs = [w / total_weight for w in action_weights]

        # Choose
        action_idx = np.random.choice(len(actions), p=action_probs)
        action, args = actions[action_idx]
        return action, args


def random_learning(sess, env, num_episodes=100, max_episode_length=100000):
    """
    Q-Learning algorithm for off-policy TD control using Function Approximation.
    Finds the optimal greedy policy while following an epsilon-greedy policy.
    Args:
        sess: Tensorflow Session object
        env: AiEnv environment
        num_episodes: Number of episodes to run for
    Returns:
        An EpisodeStats object with two numpy arrays for episode_lengths and episode_rewards.
    """

    logger = logging.getLogger('random_learning')

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

            if done or step >= max_episode_length:
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
