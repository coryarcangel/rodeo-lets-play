
from collections import deque
from enums import Action
from config import REWARD_PARAMS
from util import get_dist


class RewardCalculator():
    """
    Used to get time-sensitive rewards from AIState.
    May encourage an agent to swipe more, etc.
    """

    def __init__(self, params=REWARD_PARAMS):
        self.money_mult = params['money_mult']
        self.stars_mult = params['stars_mult']
        self.action_memory = params['action_memory']
        self.max_repeat_swipes_in_memory = params['max_repeat_swipes_in_memory']
        self.max_repeat_object_taps_in_memory = params['max_repeat_object_taps_in_memory']
        self.repeat_tap_distance_threshold = params['repeat_tap_distance_threshold']
        self.swipe_reward = params['swipe_reward']
        self.object_type_tap_rewards = params['object_type_tap_rewards']
        self.color_sig_change_reward = params['color_sig_change_reward']

        self.action_cum_reward = 0
        self.last_step_num_keys = ['swipe', 'pass', 'tap', 'double_tap', 'object_tap']
        self.mark_reset()

    def mark_reset(self):
        self.last_step_nums = {}
        for k in self.last_step_num_keys:
            self.last_step_nums[k] = -1

        self.action_history = deque(maxlen=self.action_memory)
        self.last_color_sig = None

    def get_swipe_reward(self, step_num, a_name):
        swipes_in_memory = [a for a in self.action_history if a[0] == a_name]
        if len(swipes_in_memory) < self.max_repeat_swipes_in_memory:
            return self.swipe_reward
        return 0

    def get_tap_reward(self, step_num, type, a_name, args):
        type_rewards = [r for r in self.object_type_tap_rewards if r[0] == type]
        if len(type_rewards) == 0:
            return 0

        # get nearby taps in memory
        p = (args['x'], args['y'])
        th = self.repeat_tap_distance_threshold
        taps_in_memory = [a for a in self.action_history
                          if a[0] == a_name
                          and get_dist(p, (a[1]['x'], a[1]['y'])) <= th]
        if len(taps_in_memory) < self.max_repeat_object_taps_in_memory:
            return type_rewards[0][1]
        return 0

    def get_step_reward(self, step_num, ai_state, action_name, args):
        if ai_state is None:
            return 0

        reward = 0
        reward += (ai_state.money * self.money_mult)
        reward += (ai_state.stars * self.stars_mult)

        # add reward for color sig change
        if self.last_color_sig is not None and ai_state.color_sig != self.last_color_sig:
            self.action_cum_reward += self.color_sig_change_reward

        # add rewards for swipes / taps based on memory
        if action_name in (Action.SWIPE_LEFT, Action.SWIPE_RIGHT):
            self.last_step_nums['swipe'] = step_num
            self.action_cum_reward += self.get_swipe_reward(step_num, action_name)
        elif action_name in (Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION):
            name = 'tap' if action_name == Action.TAP_LOCATION else 'double_tap'
            self.last_step_nums[name] = step_num

            type = args['object_type'] if 'object_type' in args else 'unknown'
            if type != 'unknown':
                self.last_step_nums['object_tap'] = step_num

            self.action_cum_reward += self.get_tap_reward(step_num, type, action_name, args)
        elif action_name == Action.PASS:
            self.last_step_nums['pass'] = step_num

        reward += self.action_cum_reward

        self.action_history.append((action_name, args))
        self.last_color_sig = ai_state.color_sig

        return reward

    def get_recent_action_step_nums(self):
        recent_actions = {}
        for k in self.last_step_num_keys:
            val = self.last_step_nums[k]
            if val >= 0:
                recent_actions[k] = val
        return recent_actions
