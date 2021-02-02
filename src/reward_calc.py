
from ai_actions import Action


class RewardCalculator():
    """
    Used to get time-sensitive rewards from AIState.
    May encourage an agent to swipe more, etc.
    """

    def __init__(self,
                 money_mult=1.0,
                 stars_mult=1.0,
                 recent_swipe_threshold=20,
                 recent_swipe_reward=150):
        self.money_mult = money_mult
        self.stars_mult = stars_mult
        self.recent_swipe_threshold = recent_swipe_threshold
        self.recent_swipe_reward = recent_swipe_reward

        self.last_step_num_keys = ['swipe', 'pass', 'tap', 'double_tap']
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
                reward += self.recent_swipe_reward
            self.last_step_nums['swipe'] = step_num
        elif action_name == Action.PASS:
            self.last_step_nums['pass'] = step_num
        elif action_name == Action.TAP_LOCATION:
            self.last_step_nums['tap'] = step_num
        elif action_name == Action.DOUBLE_TAP_LOCATION:
            self.last_step_nums['double_tap'] = step_num

        return reward

    def get_recent_action_step_nums(self):
        recent_actions = {}
        for k in self.last_step_num_keys:
            val = self.last_step_nums[k]
            if val >= 0:
                recent_actions[k] = val
        return recent_actions
