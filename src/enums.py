import collections


class Action(object):
    """Enum-like iteration of all available actions"""
    PASS = 0
    RESET = 1
    SWIPE_LEFT = 2
    SWIPE_RIGHT = 3
    TAP_LOCATION = 4
    DOUBLE_TAP_LOCATION = 5


ACTIONS = [
    Action.PASS,
    Action.SWIPE_LEFT,
    Action.SWIPE_RIGHT,
    Action.TAP_LOCATION,
    Action.DOUBLE_TAP_LOCATION,
    Action.RESET
]

NUM_ACTIONS = len(ACTIONS)


class ActionShape(object):
    """Enum-like iteration of all available action-shape hueristic guesses"""
    MENU_EXIT = 'menu_exit'
    CONFIRM_OK = 'confirm_ok'
    MONEY_CHOICE = 'money_choice'
    TALK_CHOICE = 'talk_choice'
    MAYBE_TALK_CHOICE = 'maybe_talk_choice'
    ROOM_EXIT = 'room_exit'
    UNKNOWN = 'unknown'


all_action_shapes = [
    ActionShape.MENU_EXIT, ActionShape.CONFIRM_OK, ActionShape.MONEY_CHOICE,
    ActionShape.TALK_CHOICE, ActionShape.MAYBE_TALK_CHOICE, ActionShape.ROOM_EXIT, ActionShape.UNKNOWN
]


ShapeColorRange = collections.namedtuple(
    "ShapeColorRange", ['label', 'lower', 'upper', 'min_area', 'max_area', 'min_verts', 'max_verts'])
