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


class ShapeColorRange(object):
    """ used to define known color regions to look for in image_contours """

    def __init__(self,
                 action_shape,
                 color_label,
                 lower,  # Minimum HSV (Opencv scale)
                 upper,  # Maximum HSV (Opencv scale)
                 min_area=300,  # Minimum rectangular area of shape
                 max_area=10000,  # Maximum rectangular area of shape
                 min_verts=4,  # Minimum number of recognized vertices
                 max_verts=15,  # Maximum number of recognized vertices
                 min_area_ratio=0.0,  # Minimum ratio of bounds area to contour area (how "filled in" is the shape)
                 max_area_ratio=5.0):  # Maximum ratio of bounds area to contour area (how "filled in" is the shape)
        self.action_shape = action_shape
        self.color_label = color_label
        self.lower = lower
        self.upper = upper
        self.min_area = min_area
        self.max_area = max_area
        self.min_verts = min_verts
        self.max_verts = max_verts
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
