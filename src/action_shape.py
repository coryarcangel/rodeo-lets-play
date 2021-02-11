'''
We use contour detection to detect solid patches of color, which is how most
selectable bubbles in the game are detected. This section of code helps define
the types of bubbles to look for.
'''

from enums import ActionShape


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
        return ActionShape.MAYBE_TALK_CHOICE

    return ActionShape.UNKNOWN


def get_shape_data_label(shape_data, image_shape):
    ''' Returns simple formatted label of shape data if we can guess the Shape '''
    action_shape = get_shape_data_likely_action_shape(shape_data, image_shape)
    if action_shape == ActionShape.UNKNOWN:
        return None

    return '%s (%s, %s)' % (action_shape, shape_data['shape'], shape_data['color_label'])
