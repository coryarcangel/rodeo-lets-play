"""
Contains KimEnv class for controlling the game via the learning algorithm.
"""

import logging
import numpy as np
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step

from ai_actions import Action
from ai_env import DeviceClientEnvActionStateManager
from object_name_values import get_object_name_int_values
from config import REDIS_HOST, REDIS_PORT


class DeviceClientTfEnv(py_environment.PyEnvironment):
    """Environment for running KK:Hollywood. Built for Tensorflow Agents.
    https://www.tensorflow.org/agents/tutorials/2_environments_tutorial
    """

    def __init__(self, client, host=REDIS_HOST, port=REDIS_PORT):
        self.logger = logging.getLogger('KimEnv')
        self.client = client
        self.action_state_manager = DeviceClientEnvActionStateManager(
            client, host, port)

        self.num_observation_objects = 100
        self.obj_name_int_vals, self.obj_name_int_max_val = get_object_name_int_values()

        self._action_spec = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32, minimum=(), maximum=(), name='action')

        self._observation_spec = array_spec.BoundedArraySpec(
            shape=(4, self.num_observation_objects),  # a list objects with type, confidence, x, y vals
            dtype=np.int64,
            minimum=[0, 0, 0],
            maximum=[self.obj_name_int_max_val, 100, client.img_rect[2], client.img_rect[3]],
            name='observation')

        self._reward_spec = array_spec.BoundedArraySpec(
            shape=(2,),  # money, stars
            dtype=np.int64, minimum=0, name='reward')

        self._time_step_spec = time_step.time_step_spec(
            observation_spec=self._observation_spec,
            reward_spec=self._reward_spec)

    def action_spec(self):
        return self._action_spec

    def observation_spec(self):
        return self._observation_spec

    def time_step_spec(self):
        return self._time_step_spec

    def reset(self):
        """Return initial_time_step."""
        self._current_time_step = self._do_reset()
        self.logger.debug('Reset AI Environment')
        return self._current_time_step

    def step(self, action):
        """Apply action for single time step and return new time_step.
        Need to do translation work of action from numeric space to
        (action, action_args) space."""
        self._cleanup_current_step()

        if self._current_time_step is None:
            return self.reset()

        self._current_time_step = self._step(action)
        return self._current_time_step

        self.step_num += 1

        # Perform relevant action
        self._take_action(action, action_args)

        # Get new state
        self.logger.debug('Getting state for Step #%d', self.step_num)
        next_state = self._get_state()
        self.logger.debug('State for Step #%d: %s', self.step_num, next_state)

        reward = next_state.get_reward() if next_state else None
        done = False
        info = {}

        return next_state, reward, done, info

    def _get_image_object_observation_vec(self, obj):
        """Transform image_object from AIState to vector"""
        label = 'unknown'
        if 'shape_data' in obj:
            if obj['shape_data']['shape_label'] is not None:
                label = obj['shape_data']['shape_label']
        elif 'object_type' in obj:
            label = obj['object_type']
        elif 'label' in obj:
            label = obj['label']

        label_val = 0
        try:
            label_val = self.obj_name_int_vals[label]
        except Exception as _:
            label_val = self.obj_name_int_vals['unknown']

        rect = obj['rect']
        x = int(rect[0] + rect[2] * 0.5)
        y = int(rect[1] + rect[3] * 0.5)

        confidence = int(obj['confidence'] * 100) if obj['confidence'] is not None else 10

        return np.array((label_val, confidence, x, y))

    def _get_ai_state_observation(self, state):
        """Transform AIState to numpy array following observation_spec"""
        num_img_objs = len(state.image_objects)
        obj_vectors = []
        for i in range(self.num_observation_objects):
            vec = np.array((self.obj_name_int_vals['none'], 0, 0, 0))
            if i < num_img_objs:
                obj = state.image_objects[i]
                vec = self._get_image_object_observation_vec(obj)
            obj_vectors.append(vec)

        return np.array(obj_vectors)

    def _cleanup_current_step(self):
        pass

    def _do_reset(self):
        self._cleanup_current_step()
        self.client.send_reset_command()

    def _get_state(self):
        return self.action_state_manager.cur_screen_state

    def _take_action(self, action, args):
        if (action in self.action_state_manager.actions_map):
            self.action_state_manager.publish_action(action, args)
            self.action_state_manager.actions_map[action](args)
        else:
            self.logger.debug('unrecognized action %s' % action)
