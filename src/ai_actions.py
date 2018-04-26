"""Defines Constants for available game actions."""

class Action(object):
    """Enum-like iteration of all available actions"""
    PASS = 0
    SWIPE_LEFT = 1
    SWIPE_RIGHT = 2

ACTIONS = [
    Action.PASS,
    Action.SWIPE_LEFT,
    Action.SWIPE_RIGHT
]

NUM_ACTIONS = len(ACTIONS)
