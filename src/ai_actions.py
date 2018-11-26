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


def _get_object_tap_action(obj):
    x, y = get_rect_center(obj['rect'])
    return (Action.TAP_LOCATION, {
        'x': int(x),
        'y': int(y),
        'type': 'object',
        'object_label': obj['label'],
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

        return ActionGetter.Base + object_taps
