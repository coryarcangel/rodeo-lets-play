
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

        self.last_swipe_step_num = -recent_swipe_threshold

    def get_step_reward(self, step_num, ai_state, action_name, args):
        if ai_state is None:
            return 0

        reward = 0
        reward += (ai_state.money * self.money_mult)
        reward += (ai_state.stars * self.stars_mult)

        # if we swipe and haven't swiped in a while, give a reward boost.
        if action_name in (Action.SWIPE_LEFT, Action.SWIPE_RIGHT):
            if step_num - self.last_swipe_step_num >= self.recent_swipe_threshold:
                reward += self.recent_swipe_reward
            self.last_swipe_step_num = step_num

        return reward
