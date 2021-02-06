'''
We use contour detection to detect solid patches of color, which is how most
selectable bubbles in the game are detected. This section of code helps define
the types of bubbles to look for.
'''


class ActionShape(object):
    """Enum-like iteration of all available action-shape hueristic guesses"""
    MENU_EXIT = 'menu_exit'
    CONFIRM_OK = 'confirm_ok'
    MONEY_CHOICE = 'money_choice'
    TALK_CHOICE = 'talk_choice'
    UNKNOWN = 'unknown'


all_action_shapes = [
    ActionShape.MENU_EXIT, ActionShape.CONFIRM_OK, ActionShape.MONEY_CHOICE,
    ActionShape.TALK_CHOICE, ActionShape.UNKNOWN
]


# Label, Lower HSV, Upper HSV, Min Area
action_shape_color_ranges = [
    ('Light Blue', (100, 160, 50), (120, 255, 255), 2000),
    ('Light Green', (40, 100, 50), (65, 255, 255), 2000),
    ('Light Gray', (100, 50, 200), (105, 100, 255), 2000),
    ('Red', (0, 110, 225), (5, 140, 255), 60),
    ('Gold', (10, 20, 50), (30, 255, 255), 2000),
    # ('White', (0, 0, 253), (255, 1, 255), 40),
    # ('Black', (0, 0, 0), (255, 255, 20), 60),
]


def get_shape_data_likely_action_shape(shape_data, image_shape):
    ''' Gets best-guess of ActionShape from shape data (color, point, area, shape) '''
    p, a, s, co = [shape_data[k] for k in ('point', 'area', 'shape', 'color_label')]
    x, y = p
    iw, ih = image_shape[0:2]

    if co == 'Red' and a < 200:
        return ActionShape.MENU_EXIT

    centered = abs(x - iw / 2.0) < 100
    if centered and co == 'Gold':
        return ActionShape.CONFIRM_OK
    if centered and co == 'Light Green' and centered:
        return ActionShape.MONEY_CHOICE
    if centered and co in ('Light Gray', 'Light Blue'):
        return ActionShape.TALK_CHOICE

    return ActionShape.UNKNOWN


def get_shape_data_label(shape_data, image_shape):
    ''' Returns simple formatted label of shape data if we can guess the Shape '''
    action_shape = get_shape_data_likely_action_shape(shape_data, image_shape)
    if action_shape == ActionShape.UNKNOWN:
        return None

    return '%s (%s, %s)' % (action_shape, shape_data['shape'], shape_data['color_label'])
