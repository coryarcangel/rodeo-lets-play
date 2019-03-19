"""Defines Constants for available game actions."""

from config import CURRENT_IMG_CONFIG
from util import get_rect_center, Rect

img_rect = Rect(0, 0, CURRENT_IMG_CONFIG.width, CURRENT_IMG_CONFIG.height)
img_rect_center = get_rect_center(img_rect)


class Action(object):
    """Enum-like iteration of all available actions"""
    PASS = 0
    SWIPE_LEFT = 1
    SWIPE_RIGHT = 2
    TAP_LOCATION = 3


ACTIONS = [
    Action.PASS,
    Action.SWIPE_LEFT,
    Action.SWIPE_RIGHT,
    Action.TAP_LOCATION
]

NUM_ACTIONS = len(ACTIONS)


def get_action_type_str(action_type):
    if action_type == Action.PASS:
        return 'pass'
    elif action_type == Action.SWIPE_LEFT:
        return 'swipe_left'
    elif action_type == Action.SWIPE_RIGHT:
        return 'swipe_right'
    else:
        return 'tap_location'


def _get_object_tap_action(obj):
    x, y = get_rect_center(obj['rect'])
    return (Action.TAP_LOCATION, {
        'x': int(x),
        'y': int(y),
        'type': 'object',
        'object_type': obj['object_type'] if 'obj_type' in obj else obj['label'],
        'img_obj': obj
    })


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
    ] + BottomMenuTaps

    Base = [Pass] + Swipes + MenuTaps
    # Base = MenuTaps

    @classmethod
    def get_actions_from_state(cls, state):
        if not state:
            return ActionGetter.Base

        object_taps = [_get_object_tap_action(
            obj) for obj in state.image_objects]

        # return object_taps if len(object_taps) > 0 else ActionGetter.Base
        return ActionGetter.Base + object_taps


class ActionWeighter(object):
    ''' gets default action weights for weighted-random selection '''
    def __init__(self):
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
