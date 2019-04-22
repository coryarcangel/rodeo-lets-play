"""Selects actions based on predefined probabilities and according to a combination of known heuristics."""

import itertools
import logging
import numpy as np
import tensorflow as tf
import plotting
from collections import deque
from ai_actions import ActionGetter, ActionWeighter, Action, get_action_type_str

'''
    *** Complete Heuristics ***

    Heuristic #1 - Reduce In-Room Repetition
        Try to recognize when we have already tapped an object in a specific room, and reduce the likelihood
        that we tap that object again.

    *** Incomplete Heuristics ***

    Heuristic #2 - Room Memory
        Look into previous rooms in the sequence — if I have been to a room recently,
        should I be more likely to leave it soon?

    Heuristic #3 - Color Splatch Detection
        Detect large splotches of specific solid colors—those are important things to tap.

    Heuristic #4 - Have I gotten any money recently?
'''

class HeuristicRoom(object):
    ''' Maintains info for a room identified by a specific color_sig '''

    def __init__(self, color_sig, time_since_last_visit, rooms_since_last_visit):
        self.color_sig = color_sig
        self.time_since_last_visit = time_since_last_visit
        self.rooms_since_last_visit = rooms_since_last_visit

        self.reward_seq = []
        self.has_gained_money = False

        self.action_count = 0
        self.action_selection_counts = {}
        self.action_weighter = ActionWeighter()
        self.blob_dom_color_weights = {
            'red': 300,
            'green': 600,
            'blue': 1000,
            'black': 200,
            'white': 1000
        }

    def _get_action_rep(self, a_tup):
        action_type, args = a_tup
        if action_type != Action.TAP_LOCATION:
            return get_action_type_str(action_type)

        type = args['type'] if 'type' in args else 'none'
        if type != 'object':
            return 'tap_' + type

        return 'tap_object_{}_y{}'.format(args['object_type'].lower(), args['y'])

    def _have_recently_been_here(self): return self.rooms_since_last_visit < 6
    def _have_been_here_a_while(self): return self.action_count >= 300

    def _get_exit_action_weight(self):
        ''' If I have recently been to this room, or it has been forever since I have left, let's emphasize leaving '''
        if self._have_recently_been_here() or self._have_been_here_a_while():
            return 2500
        elif self._have_not_made_money_here():
            return 100
        else:
            return 500

    def _get_object_tap_default_weight(self, a_tup):
        action_type, args = a_tup
        type = args['object_type']
        if type == 'blob':
            dom_color = args['img_obj']['dom_color']
            size = args['img_obj']['size']
            color_weight = self.blob_dom_color_weights[dom_color] if dom_color in self.blob_dom_color_weights else 50
            size_mult = 2 if size > 200 else 1
            return color_weight * size_mult
        elif self.action_weighter.is_object_type_likely_exit(type):
            return self.get_exit_action_weight()
        else:
            return self.action_weighter.get_action_weight(a_tup)

    def get_action_weight(self, a_tup):
        ''' Gets weight of an action (for weighted-random selection) based on heuristics listed above '''
        action_type, args = a_tup
        is_object_tap = action_type == Action.TAP_LOCATION and 'type' in args and args['type'] == 'object'

        # The more we select an action, the less likely we are to pick it again in this room
        rep = self._get_action_rep(a_tup)
        sel_count = self.action_selection_counts[rep] if rep in self.action_selection_counts else 0
        sel_p = min(sel_count, 10) / 15.0 if is_object_tap else min(sel_count, 2) / 8.0
        depression_mult = (1 - math.pow(sel_p, 1))

        # Get unique weight for type of object tap
        default_weight = 0
        if is_object_tap:
            type = self._get_object_tap_default_weight(a_tup)
        else:
            default_weight = self.action_weighter.get_action_weight(a_tup)

        # Multiply default by the depression heuristic
        weight = default_weight * depression_mult
        return weight

    def ingest_state(self, state):
        ''' Basically just adds states rewards to reward seq for later inspection '''
        reward = state.get_reward_dict()
        self.reward_seq.push(reward)
        if not self.has_gained_money and reward['money'] > self.reward_seq[0]['money']:
            self.has_gained_money = True

    def select_from_actions(self, actions):
        ''' Selects an action from possible list based on... heuristics '''

        # Choose with custom weights
        a_tup = self.action_weighter.select_action(actions, self.get_action_weight)

        # Mark as selected
        rep = self._get_action_rep(a_tup)
        self.action_selection_counts[rep] = self.action_selection_counts[rep] + 1 if rep in self.action_selection_counts else 1
        self.action_count += 1

        return a_tup

class HeuristicActionSelector(object):
    ''' Selects action from AIState with heuristics and with weighting based on projected
    value of types of moves '''

    def __init__(self):
        self.state_room_seq = deque(maxlen=100)
        self.state_idx = 0

    def _create_room(self, state):
        # Get total action count since we have last been to this room
        has_visited_before = False
        time_since_last_visit = 0
        rooms_since_last_visit = 0
        num_rooms = max(1, len(self.state_room_seq))
        for i in range(num_rooms - 1):
            prev_room = self.state_room_seq[-(i + 1)]
            if prev_room.color_sig == state.color_sig:
                has_visited_before = True
                break
            else:
                rooms_since_last_visit += 1
                time_since_last_visit += prev_room.action_count

        # Create room
        room = HeuristicRoom(
            state.color_sig,
            time_since_last_visit if has_visited_before else 0,
            rooms_since_last_visit if has_visited_before else 0
        )
        return room

    def ingest_state_into_room(self, state):
        ''' incorporates state into state_room_seq, deciding its a new room if color_sig is different...'''
        did_change = self.state_idx == 0 or state.color_sig != self.state_room_seq[-1].color_sig
        if did_change:
            # Create room and append to seq
            room = self._create_room(state)
            self.state_room_seq.append(room)

        return self.state_room_seq[-1]

    def select_state_action(self, state):
        # Ingest state and get heuristic room
        room = self.ingest_state_into_room(state)
        room.ingest_state(state)

        # Get possible actions
        actions = ActionGetter.get_actions_from_state(state)

        # Select the action from the room
        a_tup = room.select_from_actions(actions)

        # Complete state
        self.state_idx += 1

        return a_tup


def heuristic_learning(sess, env, num_episodes=100, max_episode_length=100000):
    """
    Args:
        sess: Tensorflow Session object
        env: AiEnv environment
        num_episodes: Number of episodes to run for
    Returns:
        An EpisodeStats object with two numpy arrays for episode_lengths and episode_rewards.
    """

    logger = logging.getLogger('heuristic_learning')

    # Keeps track of useful statistics
    stats = plotting.EpisodeStats(
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
