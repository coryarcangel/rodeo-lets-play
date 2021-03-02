
from collections import deque
from enums import Action
from config import REWARD_PARAMS
from util import get_dist


class RewardCalculator():
    """
    Used to get time-sensitive rewards from AIState.
    May encourage an agent to swipe more, etc.
    Helpful: https://www.oreilly.com/radar/reinforcement-learning-explained/
    """

    def __init__(self, client, params=REWARD_PARAMS):
        self.client = client

        self.money_mult = params['money_mult']
        self.stars_mult = params['stars_mult']
        self.money_memory = params['money_memory']
        self.stars_memory = params['stars_memory']
        self.action_memory = params['action_memory']
        self.max_repeat_swipes_in_memory = params['max_repeat_swipes_in_memory']
        self.max_repeat_object_taps_in_memory = params['max_repeat_object_taps_in_memory']
        self.repeat_tap_distance_threshold = params['repeat_tap_distance_threshold']
        self.swipe_reward = params['swipe_reward']
        self.object_type_tap_rewards = params['object_type_tap_rewards']
        self.color_sig_change_reward = params['color_sig_change_reward']
        self.repeat_tap_penalty = params['repeat_tap_penalty']
        self.repeat_swipe_penalty = params['repeat_swipe_penalty']
        self.do_nothing_penalty = params['do_nothing_penalty']
        self.tap_safeguard_penalty = params['tap_safeguard_penalty']
        self.reset_penalty = params['reset_penalty']

        self.last_step_num_keys = ['swipe', 'pass', 'tap', 'double_tap', 'object_tap']
        self.mark_reset()

    def mark_reset(self):
        self.money_history = deque(maxlen=self.money_memory)
        self.stars_history = deque(maxlen=self.stars_memory)
        self.action_history = deque(maxlen=self.action_memory)
        self.last_color_sig = None

        self.last_step_nums = {}
        for k in self.last_step_num_keys:
            self.last_step_nums[k] = -1

    def get_swipe_reward(self, step_num, a_name):
        swipes_in_memory = [a for a in self.action_history if a[0] == a_name]
        if len(swipes_in_memory) < self.max_repeat_swipes_in_memory:
            return self.swipe_reward
        else:
            return self.repeat_swipe_penalty

    def get_tap_reward(self, step_num, type, a_name, args):
        # get nearby taps in memory
        x, y = (args['x'], args['y'])
        th = self.repeat_tap_distance_threshold
        taps_in_memory = [a for a in self.action_history
                          if a[0] == a_name
                          and get_dist((x, y), (a[1]['x'], a[1]['y'])) <= th]

        # penalize for too many taps in same place
        if len(taps_in_memory) >= self.max_repeat_object_taps_in_memory:
            return self.repeat_tap_penalty

        # penalize tapping in safeguarded region
        if self.client.should_safeguard_img_point(x, y):
            return self.tap_safeguard_penalty

        # penalize tapping nothing
        if type == 'unknown':
            return self.do_nothing_penalty

        # give reward for clicking given type
        type_rewards = [r for r in self.object_type_tap_rewards if r[0] == type]
        if len(type_rewards) == 0:
            return 0
        return type_rewards[0][1]

    def _get_long_term_value_delta(self, value, history):
        if len(history) == 0:
            return 0

        last_value = history[-1]
        value_delta = value - last_value
        value_in_memory = [v for v in history if v == value]
        # if value change is positive and we didnt just have this value (guard against an OCR BLIP)
        if value_delta > 0 and len(value_in_memory) == 0:
            return value_delta
        else:
            return 0

    def get_step_reward(self, step_num, ai_state, action_name, args):
        if ai_state is None:
            return 0

        reward = 0

        # add reward for new money / stars
        if ai_state.money >= 0:
            money_delta = self._get_long_term_value_delta(ai_state.money, self.money_history)
            reward += (money_delta * self.money_mult)
            self.money_history.append(ai_state.money)
        if ai_state.stars >= 0:
            stars_delta = self._get_long_term_value_delta(ai_state.stars, self.stars_history)
            reward += (stars_delta * self.stars_mult)
            self.stars_history.append(ai_state.stars)

        # add reward for color sig change
        if self.last_color_sig is not None and ai_state.color_sig != self.last_color_sig:
            reward += self.color_sig_change_reward
        self.last_color_sig = ai_state.color_sig

        # add rewards for actions based on memory
        if action_name in (Action.SWIPE_LEFT, Action.SWIPE_RIGHT):
            self.last_step_nums['swipe'] = step_num
            reward += self.get_swipe_reward(step_num, action_name)
        elif action_name in (Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION):
            name = 'tap' if action_name == Action.TAP_LOCATION else 'double_tap'
            self.last_step_nums[name] = step_num

            type = args['object_type'] if 'object_type' in args else 'unknown'
            if type != 'unknown':
                self.last_step_nums['object_tap'] = step_num

            reward += self.get_tap_reward(step_num, type, action_name, args)
        elif action_name == Action.PASS:
            self.last_step_nums['pass'] = step_num
            reward += self.do_nothing_penalty
        elif action_name == Action.RESET:
            reward += self.reset_penalty

        self.action_history.append((action_name, args))

        return reward

    def get_recent_action_step_nums(self):
        recent_actions = {}
        for k in self.last_step_num_keys:
            val = self.last_step_nums[k]
            if val >= 0:
                recent_actions[k] = val
        return recent_actions
