"""Selects actions based on predefined probabilities and according to a combination of known heuristics."""

import itertools
import logging
import numpy as np
import tensorflow as tf
import plotting
from collections import deque
from math import pow
from ai_actions import ActionGetter, ActionWeighter, Action, get_action_type_str
from action_shape import ActionShape, get_shape_data_likely_action_shape


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


class HeuristicConfig(object):
    ''' Contains configuration variables for experimenting with the
        Heuristic Action Selector. '''

    def __init__(self):
        # Toggle on / off specific heuristic usage
        self.REPEAT_ACTION_DEPRESS = True
        self.RECENT_ROOM_MEMORY = True
        self.COLOR_ACTION_DETECT = True

        self.max_room_history_len = 100

        # What is the maximum number of times I might expect to select the same action in a given room?
        self.object_tap_action_max_sel_count = 5
        self.other_action_max_sel_count = 2

        # What should the denominator be when determining a_sel_count depression mult?
        self.object_tap_action_sel_denom = 15.0
        self.other_action_sel_denom = 8.0

        # How aggressively should I depress repeated actions (lower is more aggressive)
        self.action_sel_depress_exp = 1.0

        # How many frames do I need to wait on the same exact screen before resetting?
        self.image_sig_stag_limit = 50

        # Probabalistic weights to assign to found blobs of given colors
        self.blob_dom_color_weights = {
            'red': 300,
            'green': 600,
            'blue': 1000,
            'black': 200,
            'white': 1000,
            'other': 80
        }

        # Probabalistic weights to assign to best-guess of ActionShape variety
        self.action_shape_tap_weights = {
            ActionShape.MENU_EXIT: 10000,
            ActionShape.CONFIRM_OK: 10000,
            ActionShape.MONEY_CHOICE: 300,
            ActionShape.TALK_CHOICE: 2500,
            ActionShape.UNKNOWN: 100
        }

        # How big does a blob need to be to pass the "large" filter
        self.large_blob_threshold = 200

        # How much more should I emphasize large blobs
        self.large_blob_weight_mult = 2

        # How many rooms should I look back to see if I have recently been here?
        self.recent_room_threshold = 6

        # What should the weight of exiting be if I have just been to this room?
        self.recent_room_exit_weight = 2500

        # How many actions do I need to take in this room before I should look to leave?
        self.same_room_threshold = 300

        # What should the weight of exiting be if I:
        self.recent_room_exit_weight = 2500  # have just been to this room
        self.same_room_exit_weight = 2500  # have been in this room a while?
        self.no_money_exit_weight = 100  # have not made money in this room
        self.default_exit_weight = 500  # default

    def get_blob_color_weight(self, color):
        weights = self.blob_dom_color_weights
        return weights[color] if color in weights else weights['other']

    def get_blob_size_mult(self, size):
        return self.large_blob_weight_mult if size > self.large_blob_threshold else 1

    def get_action_shape_tap_weight(self, action_shape):
        weights = self.action_shape_tap_weights
        return weights[action_shape] if action_shape in weights else weights[ActionShape.UNKNOWN]


class HeuristicRoom(object):
    ''' Maintains info for a room identified by a specific color_sig '''

    def __init__(self, color_sig, time_since_last_visit, rooms_since_last_visit):
        self.color_sig = color_sig
        self.time_since_last_visit = time_since_last_visit
        self.rooms_since_last_visit = rooms_since_last_visit

        self.cur_image_shape = None

        self.cur_image_sig = 0
        self.image_sig_stag_count = 0
        self.needs_reset = False

        self.reward_seq = []
        self.has_gained_money = False

        self.action_count = 0
        self.action_selection_counts = {}
        self.action_weighter = ActionWeighter()

        self.config = HeuristicConfig()

    def _get_action_rep(self, a_tup):
        action_type, args = a_tup
        if action_type != Action.TAP_LOCATION and action_type != Action.DOUBLE_TAP_LOCATION:
            return get_action_type_str(action_type)

        name = 'tap' if action_type == Action.TAP_LOCATION else 'double_tap'
        type = args['type'] if 'type' in args else 'none'
        if type != 'object':
            return name + '_' + type

        return name + '_object_{}_y{}'.format(args['object_type'].lower(), args['y'])

    def _have_recently_been_here(self):
        return self.rooms_since_last_visit < self.config.recent_room_threshold

    def _have_been_here_a_while(self):
        return self.action_count >= self.config.same_room_threshold

    def _get_exit_action_weight(self):
        ''' If I have recently been to this room, or it has been forever since I have left, let's emphasize leaving '''
        if not self.config.RECENT_ROOM_MEMORY:
            return self.config.default_exit_weight

        if self._have_recently_been_here():
            return self.config.recent_room_exit_weight
        elif self._have_been_here_a_while():
            return self.config.same_room_exit_weight
        elif self._have_not_made_money_here():
            return self.config.no_money_exit_weight
        else:
            return self.config.default_exit_weight

    def _get_blob_tap_weight(self, img_obj):
        dom_color, size = [img_obj[k] for k in ('dom_color', 'size')]
        color_weight = self.config.get_blob_color_weight(dom_color)
        size_mult = self.config.get_blob_size_mult(size)
        return color_weight * size_mult

    def _get_action_shape_tap_weight(self, img_obj):
        a_shape = get_shape_data_likely_action_shape(img_obj['shape_data'], self.cur_image_shape)
        return self.config.get_action_shape_tap_weight(a_shape)

    def _get_object_tap_default_weight(self, a_tup):
        action_type, args = a_tup
        type, img_obj = [args[k] for k in ('object_type', 'img_obj')]

        if self.config.COLOR_ACTION_DETECT and type == 'blob':
            return self._get_blob_tap_weight(img_obj)
        elif self.config.COLOR_ACTION_DETECT and type == 'action_shape':
            return self._get_action_shape_tap_weight(img_obj)
        elif self.action_weighter.is_object_type_likely_exit(type):
            return self._get_exit_action_weight()
        else:
            return self.action_weighter.get_action_weight(a_tup)

    def get_action_weight(self, a_tup):
        ''' Gets weight of an action (for weighted-random selection) based on heuristics listed above '''
        action_type, args = a_tup
        is_tap = action_type == Action.TAP_LOCATION or action_type == Action.DOUBLE_TAP_LOCATION
        is_object_tap = is_tap and 'type' in args and args['type'] == 'object'

        # The more we select an action, the less likely we are to pick it again in this room
        depression_mult = 1
        if self.config.REPEAT_ACTION_DEPRESS:
            rep = self._get_action_rep(a_tup)
            a_sel_counts = self.action_selection_counts
            sel_count = a_sel_counts[rep] if rep in a_sel_counts else 0

            sel_p = 1
            if is_object_tap:
                c = min(sel_count, self.config.object_tap_action_max_sel_count)
                sel_p = c / self.config.object_tap_action_sel_denom
            else:
                c = min(sel_count, self.config.other_action_max_sel_count)
                sel_p = c / self.config.other_action_sel_denom

            depression_mult = (1 - pow(sel_p, self.config.action_sel_depress_exp))

        # Get unique weight for type of object tap
        default_weight = 0
        if is_object_tap:
            default_weight = self._get_object_tap_default_weight(a_tup)
        else:
            default_weight = self.action_weighter.get_action_weight(a_tup)

        # Multiply default by the depression heuristic
        weight = default_weight * depression_mult
        return weight

    def _ingest_image_sig(self, image_sig):
        if image_sig == self.cur_image_sig:
            self.image_sig_stag_count += 1
            if self.image_sig_stag_count > self.config.image_sig_stag_limit:
                # reset when we have been on the same screen for a long time
                self.needs_reset = True
        else:
            self.cur_image_sig = image_sig
            self.image_sig_stag_count = 0

    def ingest_state(self, state):
        ''' Basically just adds states rewards to reward seq for later inspection '''
        self.cur_image_shape = state.image_shape

        self._ingest_image_sig(state.image_sig)

        reward = state.get_reward_dict()
        self.reward_seq.append(reward)
        if not self.has_gained_money and reward['money'] > self.reward_seq[0]['money']:
            self.has_gained_money = True

    def select_from_actions(self, actions):
        ''' Selects an action from possible list based on... heuristics '''

        if self.needs_reset:
            return (Action.RESET, {})

        # Choose with custom weights
        a_tup = self.action_weighter.select_action(actions, self.get_action_weight)

        # Mark as selected
        rep = self._get_action_rep(a_tup)

        a_sel_counts = self.action_selection_counts
        count = a_sel_counts[rep] + 1 if rep in a_sel_counts else 0
        a_sel_counts[rep] = count + 1

        self.action_count += 1

        return a_tup


class HeuristicActionSelector(object):
    ''' Selects action from AIState with heuristics and with weighting based on projected
    value of types of moves '''

    def __init__(self):
        self.config = HeuristicConfig()
        self.state_room_seq = deque(maxlen=self.config.max_room_history_len)
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

        a_probs = room.action_weighter.get_action_probs(actions, room.get_action_weight)

        # Complete state
        self.state_idx += 1

        return a_tup

    def get_state_status(self, state):
        actions = ActionGetter.get_actions_from_state(state)

        room = self.state_room_seq[-1]
        a_probs = room.action_weighter.get_action_probs(actions, room.get_action_weight)

        return {'actions': actions, 'action_probs': a_probs}


def heuristic_learning(sess, env, num_episodes=1000, max_episode_length=100000):
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
            env._publish_data('ai-status-updates', status)

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
