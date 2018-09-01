"""Defines Constants for available game actions."""

from util import get_rect_center

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


def get_actions_from_state(state):
    """ Returns list of possible (action, arg) tuples from an AIState instance. """
    base = [
        (Action.Pass, {}),
        (Action.SWIPE_LEFT, { 'distance': 20 }),
        (Action.SWIPE_RIGHT, { 'distance': 20  }),
        (Action.SWIPE_LEFT, { 'duration': 100 }),
        (Action.SWIPE_RIGHT, { 'duration': 100  })
    ]

    def get_object_tap_action(obj):
        x, y = get_rect_center(obj['rect'])
        return (Action.TAP_LOCATION, { 'x': x, 'y': y, 'img_obj': obj })
    object_taps = [get_object_tap_action(obj) for obj in state.image_objects]

    return base + object_taps
