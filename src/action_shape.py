'''
We use contour detection to detect solid patches of color, which is how most
selectable bubbles in the game are detected. This section of code helps define
the types of bubbles to look for.
'''

import collections


class ActionShape(object):
    """Enum-like iteration of all available action-shape hueristic guesses"""
    MENU_EXIT = 'menu_exit'
    CONFIRM_OK = 'confirm_ok'
    MONEY_CHOICE = 'money_choice'
    TALK_CHOICE = 'talk_choice'
    ROOM_EXIT = 'room_exit'
    UNKNOWN = 'unknown'


all_action_shapes = [
    ActionShape.MENU_EXIT, ActionShape.CONFIRM_OK, ActionShape.MONEY_CHOICE,
    ActionShape.TALK_CHOICE, ActionShape.ROOM_EXIT, ActionShape.UNKNOWN
]


ShapeColorRange = collections.namedtuple(
    "ShapeColorRange", ['label', 'lower', 'upper', 'min_area', 'max_area', 'min_verts', 'max_verts'])


# still seeking: purple
action_shape_color_ranges = [
    ShapeColorRange('Light Blue', (100, 160, 50), (120, 255, 255), 200, 1400, 4, 12),
    ShapeColorRange('Light Green', (40, 100, 50), (65, 255, 255), 100, 1600, 4, 12),
    ShapeColorRange('Pink', (160, 20, 20), (170, 255, 255), 100, 1400, 4, 12),
    ShapeColorRange('Orange', (14, 50, 200), (15, 255, 255), 200, 1400, 4, 12),
    ShapeColorRange('Light Gray', (100, 50, 200), (105, 100, 255), 400, 1400, 4, 12),
    ShapeColorRange('Light Gray', (0, 15, 170), (255, 25, 195), 400, 1400, 4, 12),
    ShapeColorRange('Red', (0, 100, 200), (1, 255, 255), 40, 600, 4, 12),
    ShapeColorRange('Red', (0, 25, 150), (1, 255, 255), 120, 200, 11, 30),
    ShapeColorRange('Yellow', (23, 100, 50), (30, 255, 255), 80, 1000, 4, 30),
    ShapeColorRange('Teal', (90, 150, 50), (95, 255, 200), 40, 1600, 4, 25),
    ShapeColorRange('White', (0, 0, 128), (255, 5, 255), 80, 400, 4, 30),
]


def get_shape_data_likely_action_shape(shape_data, image_shape):
    ''' Gets best-guess of ActionShape from shape data (color, point, area, shape) '''
    p, a, v, s, co = [shape_data[k] for k in ('point', 'rawArea', 'verts', 'shape', 'color_label')]
    x, y = p
    iw, ih = image_shape[0:2]
    # centered = abs(x - iw / 2.0) < 100

    if co == 'Red' and a < 115 and v <= 12:
        return ActionShape.MENU_EXIT
    if co == 'Red' and a < 200 and v >= 11:
        return ActionShape.ROOM_EXIT
    if co == 'Gold':
        return ActionShape.CONFIRM_OK
    if co == 'Light Green':
        return ActionShape.MONEY_CHOICE
    if co in ('Light Gray', 'Light Blue', 'Pink', 'Yellow'):
        return ActionShape.TALK_CHOICE
    if co == 'White' and v >= 10:  # white circle with "..."
        return ActionShape.TALK_CHOICE

    return ActionShape.UNKNOWN


def get_shape_data_label(shape_data, image_shape):
    ''' Returns simple formatted label of shape data if we can guess the Shape '''
    action_shape = get_shape_data_likely_action_shape(shape_data, image_shape)
    if action_shape == ActionShape.UNKNOWN:
        return None

    return '%s (%s, %s)' % (action_shape, shape_data['shape'], shape_data['color_label'])
