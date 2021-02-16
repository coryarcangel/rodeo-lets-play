"""Defines Constants for available game actions."""

from enums import Action
from config import CURRENT_IMG_CONFIG
from config import ACTION_WEIGHTS, TAP_TYPE_ACTION_WEIGHTS, TAP_OBJECT_ACTION_WEIGHTS

from util import get_rect_center, get_noisy_rect_center, Rect
import numpy as np

img_rect = Rect(0, 0, CURRENT_IMG_CONFIG.width, CURRENT_IMG_CONFIG.height)
img_rect_center = get_rect_center(img_rect)


def get_action_type_str(action_type):
    if action_type == Action.PASS:
        return 'pass'
    elif action_type == Action.SWIPE_LEFT:
        return 'swipe_left'
    elif action_type == Action.SWIPE_RIGHT:
        return 'swipe_right'
    elif action_type == Action.RESET:
        return 'reset'
    elif action_type == Action.DOUBLE_TAP_LOCATION:
        return 'double_tap_location'
    elif action_type == Action.TAP_LOCATION:
        return 'tap_location'
    else:
        return 'uknown - ' + str(action_type)


def get_object_action_data(obj):
    x, y = get_noisy_rect_center(obj['rect'], 0.15)
    return {
        'x': int(x),
        'y': int(y),
        'type': 'object',
        'object_type': obj['object_type'] if 'object_type' in obj else obj['label'],
        'img_obj': obj
    }


class ActionGetter(object):
    Pass = (Action.PASS, {})
    Swipes = [
        (Action.SWIPE_LEFT, {'distance': 400}),
        (Action.SWIPE_RIGHT, {'distance': 400}),
    ]
    BottomMenuTaps = [(Action.TAP_LOCATION,
                       {'type': 'menu',
                        'x': img_rect.w - 80 - 51 * i,
                        'y': img_rect.h - 28}) for i in range(4)]
    MenuTaps = [
        # For pressing the "OK"
        (Action.TAP_LOCATION,
         {'type': 'menu',
          'x': img_rect_center.x,
          'y': img_rect_center.y + 35}),
    ]
    # MenuTaps += BottomMenuTaps

    Base = [Pass] + Swipes + MenuTaps
    # Base = MenuTaps

    @classmethod
    def get_actions_from_state(cls, state):
        if not state:
            return ActionGetter.Base

        def get_tap(obj):
            return (Action.TAP_LOCATION, get_object_action_data(obj))

        def get_dbl_tap(obj):
            return (Action.DOUBLE_TAP_LOCATION, get_object_action_data(obj))

        obj_taps = [get_tap(obj) for obj in state.image_objects]
        obj_dbl_taps = [get_dbl_tap(obj) for obj in state.image_objects]

        return ActionGetter.Base + obj_taps + obj_dbl_taps


class ActionWeighter(object):
    ''' gets default action weights for weighted-random selection '''

    def __init__(self):
        self.ActionWeights = ACTION_WEIGHTS
        self.double_tap_to_tap_ratio = float(self.ActionWeights[Action.DOUBLE_TAP_LOCATION]) / self.ActionWeights[Action.TAP_LOCATION]
        self.TapTypeWeights = TAP_TYPE_ACTION_WEIGHTS
        self.TapObjectTypeWeights = TAP_OBJECT_ACTION_WEIGHTS

    def is_object_type_likely_exit(self, object_type):
        return object_type == 'circle' or object_type == 'clock' or object_type == 'frisbee'

    def get_tap_action_weight_ratio(self, action):
        return 1 if action == Action.TAP_LOCATION else self.double_tap_to_tap_ratio

    def get_action_weight(self, a_tup):
        ''' Assigns a weight to action based on its type / content '''
        action, args = a_tup
        action_type = args['type'] if 'type' in args else None
        object_type = args['object_type'].lower() if 'object_type' in args else None
        is_tap = action == Action.TAP_LOCATION or action == Action.DOUBLE_TAP_LOCATION

        if is_tap and action_type in self.TapTypeWeights:
            base_weight = self.TapTypeWeights[action_type]
            if object_type and object_type in self.TapObjectTypeWeights:
                base_weight = self.TapObjectTypeWeights[object_type]
            return self.get_tap_action_weight_ratio(action) * base_weight
        if action in self.ActionWeights:
            return self.ActionWeights[action]
        return 1

    def get_action_probs(self, actions, get_weight):
        ''' Create list of probabilities assocaited with each action based on weight '''
        action_weights = [get_weight(a) for a in actions]
        total_weight = float(sum(action_weights))
        action_probs = [w / total_weight for w in action_weights]
        return action_probs

    def _select_action_from_probs(self, actions, action_probs):
        action_idx = np.random.choice(len(actions), p=action_probs)
        action, args = actions[action_idx]
        args['action_prob'] = action_probs[action_idx]
        return (action, args)

    def select_action(self, actions, get_weight):
        ''' Selects action from list based on weight provided from get_weight fn '''

        # Assign weighted probabilities
        action_probs = self.get_action_probs(actions, get_weight)

        # Choose
        return self._select_action_from_probs(actions, action_probs)
