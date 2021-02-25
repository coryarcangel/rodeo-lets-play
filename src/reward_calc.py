
from enums import Action
from config import REWARD_PARAMS


class RewardCalculator():
    """
    Used to get time-sensitive rewards from AIState.
    May encourage an agent to swipe more, etc.
    """

    def __init__(self,
                 money_mult=REWARD_PARAMS['money_mult'],
                 stars_mult=REWARD_PARAMS['stars_mult'],
                 recent_swipe_threshold=REWARD_PARAMS['recent_swipe_threshold'],
                 swipe_reward=REWARD_PARAMS['swipe_reward'],
                 recent_object_tap_threshold=REWARD_PARAMS['recent_object_tap_threshold'],
                 object_tap_reward=REWARD_PARAMS['object_tap_reward']):
        self.money_mult = money_mult
        self.stars_mult = stars_mult
        self.recent_swipe_threshold = recent_swipe_threshold
        self.swipe_reward = swipe_reward
        self.recent_object_tap_threshold = recent_object_tap_threshold
        self.object_tap_reward = object_tap_reward

        self.action_cum_reward = 0
        self.last_step_num_keys = ['swipe', 'pass', 'tap', 'double_tap', 'object_tap']
        self.mark_reset()

    def mark_reset(self):
        self.last_step_nums = {}
        for k in self.last_step_num_keys:
            self.last_step_nums[k] = -self.recent_swipe_threshold

    def get_step_reward(self, step_num, ai_state, action_name, args):
        if ai_state is None:
            return 0

        reward = 0
        reward += (ai_state.money * self.money_mult)
        reward += (ai_state.stars * self.stars_mult)

        # if we swipe and haven't swiped in a while, give a reward boost.
        if action_name in (Action.SWIPE_LEFT, Action.SWIPE_RIGHT):
            if step_num - self.last_step_nums['swipe'] >= self.recent_swipe_threshold:
                self.action_cum_reward += self.swipe_reward
            self.last_step_nums['swipe'] = step_num
        elif action_name == Action.PASS:
            self.last_step_nums['pass'] = step_num
        elif action_name == Action.TAP_LOCATION:
            self.last_step_nums['tap'] = step_num
            if 'object_type' in args and args['object_type'] != 'deep_q':
                if step_num - self.last_step_nums['object_tap'] >= self.recent_object_tap_threshold:
                    self.action_cum_reward += self.object_tap_reward
                self.last_step_nums['object_tap'] = step_num
        elif action_name == Action.DOUBLE_TAP_LOCATION:
            self.last_step_nums['double_tap'] = step_num

        reward += self.action_cum_reward

        return reward

    def get_recent_action_step_nums(self):
        recent_actions = {}
        for k in self.last_step_num_keys:
            val = self.last_step_nums[k]
            if val >= 0:
                recent_actions[k] = val
        return recent_actions
