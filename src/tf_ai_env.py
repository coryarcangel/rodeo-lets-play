"""
Contains KimEnv class for controlling the game via the learning algorithm.
"""

import json
import logging
import numpy as np
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step

from ai_actions import Action, get_object_action_data, get_action_type_str
from ai_state_data import AIState
from env_action_state_manager import DeviceClientEnvActionStateManager
from object_name_values import get_object_name_int_values
from config import REDIS_HOST, REDIS_PORT


class DeviceClientTfEnv(py_environment.PyEnvironment):
    """Environment for running KK:Hollywood. Built for Tensorflow Agents.
    https://www.tensorflow.org/agents/tutorials/2_environments_tutorial
    """

    def __init__(self, client, host=REDIS_HOST, port=REDIS_PORT):
        self.logger = logging.getLogger('TfKimEnv')
        self.client = client
        self.action_state_manager = DeviceClientEnvActionStateManager(
            client, host, port)

        # [0,1] domain, lower makes next step reward less important
        self.std_discount = 0.5

        self.num_observation_objects = 100
        self.obj_name_int_vals, self.obj_name_int_max_val = get_object_name_int_values()

        max_width = client.img_rect[2]
        max_height = client.img_rect[3]

        bf = self.grid_blur_factor = 4
        blur_width = self.blur_width = int(max_width / bf)
        blur_height = self.blur_height = int(max_height / bf)
        self.max_action_vals_1 = [5, blur_width, blur_height]
        self.max_action_vals_2 = 3 + (2 * blur_width) + (2 * blur_height)

        # Type 1 - (action, x, y) (blurred)
        self._action_spec_1 = array_spec.BoundedArraySpec(
            shape=(3,), dtype=np.int32,
            minimum=[0, 0, 0], maximum=self.max_action_vals_1, name='action')

        # Type 2 - int like P, SL, SR, R, T00, T01, ..., T10, T11, ..., DT00,
        self._action_spec_2 = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32,
            minimum=0, maximum=self.max_action_vals_2, name='action')

        # a list objects with type, confidence, x, y vals
        self._observation_spec = array_spec.BoundedArraySpec(
            shape=(self.num_observation_objects, 4),
            dtype=np.int32,
            minimum=[(0, 0, 0, 0)],
            maximum=[self.obj_name_int_max_val, 100, max_width, max_height],
            name='observation')

    """ Implementing TF-Agent PyEnvironment Abstract Methods """

    def action_spec(self):
        return self._action_spec_1

    def observation_spec(self):
        return self._observation_spec

    def _reset(self):
        self.logger.debug('Reset AI Environment')
        self._cleanup_current_step()
        self.client.reset_game()
        self.step_num = 0
        return time_step.restart(self._get_empty_tf_obs())

    def _step(self, tf_action):
        """Apply action for single time step and return new time_step.
        Need to do translation work of action from numeric space to
        (action, action_args) space."""

        self._cleanup_current_step()

        self.step_num += 1

        action_name, args = self.tf_action_to_ai_action(tf_action)

        self.logger.debug('Step %d - Taking Action (%s, %s)',
            self.step_num, get_action_type_str(action_name), json.dumps(args))

        if action_name == Action.RESET:
            return self.reset()

        self._take_ai_action(action_name, args)

        observation = self._get_current_tf_obs()
        reward = self._get_ai_state_reward()

        self.logger.debug('Step %d - Reward %d', self.step_num, reward)

        return time_step.transition(
            observation, reward=reward, discount=self.std_discount)

    """ Transforming AIStateData to TF-Agent Observation """

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

        return np.array((label_val, confidence, x, y), dtype=np.int32)

    def ai_state_to_observation(self, state):
        """Transform AIState to numpy array following observation_spec"""
        num_img_objs = len(state.image_objects)
        obj_vectors = []
        for i in range(self.num_observation_objects):
            vec = np.array((self.obj_name_int_vals['none'], 0, 0, 0), dtype=np.int32)
            if i < num_img_objs:
                obj = state.image_objects[i]
                vec = self._get_image_object_observation_vec(obj)
            obj_vectors.append(vec)

        return np.array(obj_vectors, dtype=np.int32)

    def observation_to_ai_state(self, observation):
        # TODO: do I need the reverse transformation?
        pass

    def get_cur_ai_state(self):
        return self.action_state_manager.cur_screen_state

    def _get_current_tf_obs(self):
        ai_state = self.get_cur_ai_state()
        return self.ai_state_to_observation(ai_state)

    def _get_empty_tf_obs(self):
        empty_state = AIState()
        return self.ai_state_to_observation(empty_state)

    def _cleanup_current_step(self):
        pass

    """ Getting Reward from State """

    def _get_ai_state_reward(self, ai_state=None):
        if ai_state is None:
            ai_state = self.get_cur_ai_state()
        return ai_state.get_reward()

    # Implement this if my reward spec is unusual (it doesnt have to be)
    # self._reward_spec = array_spec.BoundedArraySpec(
    #     shape=(2,),  # money, stars
    #     dtype=np.int64, minimum=0, name='reward')
    # def reward_spec(self):
    #     return self._reward_spec

    """ Transforming Actions to and from TF-Agent matrices """

    def tf_action_to_ai_action(self, tf_action):
        # Could switch this if we are using tfaction2 mode
        return self._tf_action1_to_ai_action(tf_action)

    def ai_action_to_tf_action(self, ai_action_tup):
        action, args = ai_action_tup
        return self._ai_action_to_tf_action1(action, args)

    def _get_tap_action(self, action_name, x_blur, y_blur):
        x, y = (x_blur * self.grid_blur_factor, y_blur * self.grid_blur_factor)

        ai_state = self.get_cur_ai_state()
        img_obj = ai_state.find_object_from_point(x, y) if ai_state else None

        action_data = get_object_action_data(img_obj) if img_obj else {
            'x': int(x),
            'y': int(y),
            'type': 'object',
            'object_type': 'deep_q',
            'img_obj': {'confidence': 0.1}
        }
        return (action_name, action_data)

    def _get_swipe_action(self, action_name):
        return (action_name, {'distance': 400})

    def _tf_action1_to_ai_action(self, tf_action1):
        action_name, x_blur, y_blur = tf_action1[0:3]
        if action_name in [Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION]:
            return self._get_tap_action(action_name, x_blur, y_blur)
        elif action_name in [Action.SWIPE_LEFT, Action.SWIPE_RIGHT]:
            return self._get_swipe_action(action_name)
        elif action_name in [Action.PASS, Action.RESET]:
            # reset only is reset if x and y are also zero :)
            # prevents random policy / untrained deep q from too many resets
            return (action_name, {}) if x_blur == 0 and y_blur == 0 else (Action.PASS, {})
        else:
            return (Action.PASS, {})

    def _tf_action2_to_ai_action(self, tf_action2):
        if tf_action2 in [Action.SWIPE_LEFT, Action.SWIPE_RIGHT]:
            return self._get_swipe_action(tf_action2)
        elif tf_action2 in [Action.PASS, Action.RESET]:
            return (tf_action2, {})
        else:
            # convert single digit to coded action, x, y value (see above docs)
            val = tf_action2 - 4
            bw, bh = (self.blur_width, self.blur_height)
            midpoint = bw * bh
            action_name = Action.TAP_LOCATION \
                if val <= midpoint else Action.DOUBLE_TAP_LOCATION
            grid_val = val if val <= midpoint else val - midpoint
            x_blur = int(grid_val / bw)
            y_blur = grid_val % bw
            return self._get_tap_action(action_name, x_blur, y_blur)

    def _get_ai_action_blur_grid_point(self, action_val, args):
        hasxy = action_val in [Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION]
        x, y = [args[k] for k in ('x', 'y')] if hasxy else (0, 0)
        x_blur, y_blur = [int(v) / self.grid_blur_factor for v in (x, y)]
        return x_blur, y_blur

    def _ai_action_to_tf_action1(self, action_val, args):
        x_blur, y_blur = self._get_ai_action_blur_grid_point(action_val, args)
        return np.array((action_val, x_blur, y_blur), dtype=np.int32)

    def _ai_action_to_tf_action2(self, action_val, args):
        x_blur, y_blur = self._get_ai_action_blur_grid_point(action_val, args)
        grid_val = (x_blur * self.blur_width) + y_blur  # 0-val if not tap
        multiplier = 2 if action_val == Action.DOUBLE_TAP_LOCATION else 1
        val = action_val + (grid_val * multiplier)
        return val

    def _take_ai_action(self, action, args):
        self.action_state_manager.attempt_action(action, args)
