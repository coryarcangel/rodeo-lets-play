import os

from action_shape import all_action_shapes


def get_object_name_int_values():
    """ returns a dict mapping all known object names to integer values """

    image_names = []
    image_names_file = os.getcwd() + '/../cfg/coco.names'
    with open(image_names_file) as f:
        lines = f.readlines()
        image_names = [x.strip() for x in lines if len(x.strip()) > 0]

    name_values = {}
    cur_val = 0

    other_names = ['none', 'unknown', 'circle', 'blob']
    for name in other_names:
        name_values[name] = cur_val
        cur_val += 1

    for name in image_names:
        name_values[name] = cur_val
        cur_val += 1

    for shape in all_action_shapes:
        name_values[name] = cur_val
        cur_val += 1

    return name_values, max_val
