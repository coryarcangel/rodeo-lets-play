"""Defines Constants for available game actions."""


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
    return [
        (Action.Pass, {}),
        (Action.SWIPE_LEFT, {}),
        (Action.SWIPE_RIGHT, {})
    ]
