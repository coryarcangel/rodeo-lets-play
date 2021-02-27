""" Code to store images from KK:Hollywood as data state """

import json
import random
import numpy as np
# import tensorflow as tf
from kim_logs import get_kim_logger
from enums import all_action_shapes


def get_random_object_type():
    types = [
        'person', 'clock', 'tvmonitor', 'laptop', 'traffic light',
        'Circle', 'Blob',
    ] + all_action_shapes
    return random.choice(types)


def get_random_phone_image_state(index):
    return {
        'index': index,
        'state': AIState.get_random_state()
    }


class AIState(object):
    """
    Incorporates all known information about a frame of KK:H, including:
        * image -
        * money - number
        * stars - number
        * image_objects - list of {
            label: str,
            confidence: num,
            rect: (x,y,w,h)
          } objects
    """

    def __init__(self,
                 image_shape=None,
                 money=0,
                 stars=0,
                 image_objects=None,
                 tap_circles=[],
                 color_features=None,
                 blobs=[],
                 shapes=[]):
        self.logger = get_kim_logger('AIState')
        self.image_shape = image_shape
        self.money = money
        self.stars = stars
        # self.image = tf.placeholder(shape=image_shape, dtype=tf.uint8)
        self.color_features = color_features
        self.color_sig = color_features['color_sig'] if color_features is not None and 'color_sig' in color_features else 'none'  # rough idea of colors in room
        self.image_sig = color_features['image_sig'] if color_features is not None and 'image_sig' in color_features else 'none'  # hard idea of exact image -- should change frame to frame
        self.image_objects = image_objects if image_objects is not None else []

        for idx, c in enumerate(tap_circles):
            x, y, r = c
            self.image_objects.append({
                'label': 'Circle #%d' % (idx + 1),
                'object_type': 'circle',
                'radius': r,
                'confidence': None,
                'rect': (x - r, y - r, 2 * r, 2 * r)
            })

        for idx, b in enumerate(blobs):
            x, y = b['point']
            r = int(b['size'] / 2.0)
            # TODO: can make object type stronger based on color / size of blob
            self.image_objects.append({
                'label': 'Blob #%d - %s' % (idx + 1, b['dom_color']),
                'object_type': 'blob',
                'confidence': None,
                'dom_color': b['dom_color'],
                'size': b['size'],
                'circle': (x, y, r),
                'rect': (x - r, y - r, 2 * r, 2 * r)
            })

        for idx, shape in enumerate(shapes):
            a, s, co, ashape, raw, v = [shape[k] for k in ('area', 'shape', 'color_label', 'action_shape', 'boundsArea', 'verts')]
            shape_data = { k: shape[k] for k in ('area', 'verts', 'shape', 'color_label', 'action_shape', 'boundsArea') }
            shape_data['shape_label'] = '%s (%s, %s, %d, %d)' % (ashape, s, co, v, raw)
            self.image_objects.append({
                'label': '%s (%d) - %s' % (s, a, co),
                'object_type': 'action_shape',
                'confidence': None,
                'shape_data': shape_data,
                # 'contour': c,
                'rect': shape['rect'],
            })

    @classmethod
    def deserialize(cls, data):
        ''' loads AIState from serialized json '''
        return cls(**json.loads(data))

    @classmethod
    def get_random_state(cls):
        ''' creates a test random ai_state '''
        image_shape = (640, 480)

        num_objects = random.randint(1, 10)
        object_types = [get_random_object_type() for i in range(num_objects)]
        image_objects = [{
            'label': obj_type,
            'object_type': obj_type,
            'confidence': random.random(),
            'rect': (
                random.randint(0, image_shape[0] - 100),
                random.randint(0, image_shape[1] - 100),
                random.randint(0, 100),
                random.randint(0, 100)
            )
        } for obj_type in object_types]

        return cls(
            image_shape=image_shape,
            money=random.randint(0, 1000),
            stars=random.randint(0, 500),
            image_objects=image_objects,
        )

    def __str__(self):
        return 'Money: {} | Stars: {}'.format(self.money, self.stars)

    def get_reward_dict(self):
        return {
            'money': self.money,
            'stars': self.stars,
        }

    def serialize(self):
        ''' serializes AIState into json '''

        def clean_img_obj(o):
            o2 = dict(o)
            for k in ['contour']:
                if k in o2:
                    del o2[k]
            return o2

        return json.dumps({
            'money': self.money,
            'stars': self.stars,
            'color_features': self.color_features,
            'image_objects': [clean_img_obj(o) for o in self.image_objects],
            'image_shape': self.image_shape
        })

    def get_reward(self):
        """ Returns total value of state """
        return self.money + self.stars

    def log(self):
        """ Logs string representation of state to INFO """
        self.logger.info(self)

    def to_input(self):
        """ Converts high-level object into numbers with shape STATE_INPUT_SHAPE """
        return np.array([1, self.money, self.stars])

    def find_nearest_object(self, x, y, dist_threshold):
        min_dist, min_obj = (1000000, None)
        for obj in self.image_objects:
            x1, y1, _, _ = obj['rect']
            xd, yd = (x - x1, y - y1)
            dist = (xd * xd) + (yd * yd)
            if dist < min_dist:
                min_dist = dist
                min_obj = obj

        return (min_obj, min_dist) if min_dist < dist_threshold else (None, dist_threshold)
