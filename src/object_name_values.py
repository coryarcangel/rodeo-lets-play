import os

from enums import all_action_shapes


def get_object_name_int_values():
    """
        returns:
            a dict mapping all known object names to integer values
            a dict mapping integer values to object names
            the max integer value
    """

    image_names = []

    my_dir = os.path.dirname(os.path.realpath(__file__))
    image_names_file = my_dir + '/../cfg/coco.names'
    with open(image_names_file) as f:
        lines = f.readlines()
        image_names = [x.strip() for x in lines if len(x.strip()) > 0]

    other_names = ['none', 'unknown', 'circle', 'blob']

    all_names = other_names + image_names + all_action_shapes

    name_values = {}
    value_names = {}
    cur_val = 0

    for name in all_names:
        name_values[name] = cur_val
        value_names[cur_val] = name
        cur_val += 1

    return name_values, value_names, cur_val
