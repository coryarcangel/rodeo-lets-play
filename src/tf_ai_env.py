"""
Contains KimEnv class for controlling the game via the learning algorithm.
"""

import json
import numpy as np
import random
from tf_agents.environments import py_environment
from tf_agents.specs import array_spec
from tf_agents.trajectories import time_step

from kim_logs import get_kim_logger
from enums import Action
from ai_actions import get_object_action_data, get_action_type_str
from ai_state_data import AIState
from env_action_state_manager import DeviceClientEnvActionStateManager
from reward_calc import RewardCalculator
from object_name_values import get_object_name_int_values
from config import REDIS_HOST, REDIS_PORT, ACTION_WEIGHTS, ALLOW_RESET_ACTION
from util import get_rect_center


class DeviceClientTfEnv(py_environment.PyEnvironment):
    """Environment for running KK:Hollywood. Built for Tensorflow Agents.
    https://www.tensorflow.org/agents/tutorials/2_environments_tutorial
    """

    def __init__(self, client, host=REDIS_HOST, port=REDIS_PORT):
        self.logger = get_kim_logger('TfKimEnv')
        self.client = client
        self.action_state_manager = DeviceClientEnvActionStateManager(
            client, host, port)
        self.action_spec_mode = 3  # 1 (matrix) or 2 (vector) or 3 (vector, just single tap)
        self.obs_spec_mode = 2  # 1 for list of objects, 2 for grid with obj int

        # [0,1] domain, lower makes next step reward less important
        self.std_discount = 0.5
        self.reward_calculator = RewardCalculator(client=client)

        self.num_observation_objects = 100
        self.step_num_obs_mod = 110
        self.obj_name_int_vals, self.obj_int_val_names, self.obj_name_int_max_val = get_object_name_int_values()

        grid_width = self.grid_width = 30
        grid_height = self.grid_height = 20
        grid_area = self.grid_area = grid_width * grid_height

        self.os2_overwrite_prob = 0.5

        tap_weight = float(ACTION_WEIGHTS[Action.TAP_LOCATION])
        dtap_weight = float(ACTION_WEIGHTS[Action.DOUBLE_TAP_LOCATION])
        self.as3_dtap_prob = dtap_weight / (tap_weight + dtap_weight)

        client_width = self.client_width = client.img_rect[2]
        client_height = self.client_height = client.img_rect[3]
        self.client_width_factor = float(client_width) / float(grid_width)
        self.client_height_factor = float(client_height) / float(grid_height)

        # 6 actions
        self.max_action_vals_1 = [5, grid_width - 1, grid_height - 1]

        # allow more than just two swipe actions so the algo can easily
        # discover value of swiping
        self.num_as2_actions_per_swipe = 50
        self.total_as2_swipe_actions = self.num_as2_actions_per_swipe * 2
        self.num_as3_actions_per_swipe = 10
        self.total_as3_swipe_actions = self.num_as3_actions_per_swipe * 2

        # 1 is for reset and pass, then count swipes, then grid_area * 2
        # is for tap and double_tap in each space
        self.max_action_vals_2 = 1 + self.total_as2_swipe_actions + (grid_area * 2)
        self.max_action_vals_3 = 1 + self.total_as3_swipe_actions + grid_area

        # Type 1 - (action, x, y)
        self._action_spec_1 = array_spec.BoundedArraySpec(
            shape=(3,), dtype=np.int32,
            minimum=[0, 0, 0], maximum=self.max_action_vals_1, name='action')

        # Type 2 - int like P, SL, SR, R, T00, T01, ..., T10, T11, ..., DT00,
        self._action_spec_2 = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32,
            minimum=0, maximum=self.max_action_vals_2, name='action')

        self._action_spec_3 = array_spec.BoundedArraySpec(
            shape=(), dtype=np.int32,
            minimum=0, maximum=self.max_action_vals_3, name='action')

        # step num % step_num_obs_mod, follwed by a list objects with type, confidence, x, y vals
        self._observation_spec_1 = array_spec.BoundedArraySpec(
            shape=(self.num_observation_objects + 1, 4),
            dtype=np.int32,
            minimum=[(0, 0, 0, 0)],
            maximum=[(max(self.step_num_obs_mod, self.obj_name_int_max_val), 100, grid_width, grid_height)],
            name='observation')

        # grid_x by grid_y, each with object type and confidence vals
        self._observation_spec_2 = array_spec.BoundedArraySpec(
            shape=(self.grid_width, self.grid_height, 2),
            dtype=np.int32,
            minimum=[0, 0],
            maximum=[(max(150, self.obj_name_int_max_val), 100)],
            name='observation')

        self.total_step_num = 0
        self.step_num = 0
        self.most_recent_reward = 0

    """ Implementing TF-Agent PyEnvironment Abstract Methods """

    def action_spec(self):
        if self.action_spec_mode == 1:
            return self._action_spec_1
        elif self.action_spec_mode == 2:
            return self._action_spec_2
        elif self.action_spec_mode == 3:
            return self._action_spec_3
        else:
            return None

    def observation_spec(self):
        if self.obs_spec_mode == 1:
            return self._observation_spec_1
        elif self.obs_spec_mode == 2:
            return self._observation_spec_2
        else:
            return None

    def _reset(self):
        self.logger.debug('Reset AI Environment')
        self._cleanup_current_step()
        self.client.reset_game()
        self.reward_calculator.mark_reset()
        self.step_num = 0
        return time_step.restart(self._get_empty_tf_obs())

    def _step(self, tf_action):
        """Apply action for single time step and return new time_step.
        Need to do translation work of action from numeric space to
        (action, action_args) space."""

        self._cleanup_current_step()

        self.total_step_num += 1
        self.step_num += 1

        action_name, args = self.tf_action_to_ai_action(tf_action)

        self.logger.debug('Step %d (%d) - Action (%s, %s)',
            self.step_num, self.total_step_num,
            get_action_type_str(action_name), json.dumps(args))

        if action_name == Action.RESET:
            if ALLOW_RESET_ACTION:
                return self.reset()

        if action_name != Action.RESET:
            self._take_ai_action(action_name, args)

        observation = self._get_current_tf_obs()

        reward = self.reward_calculator.get_step_reward(
            self.step_num, self.get_cur_ai_state(), action_name, args)
        self.most_recent_reward = reward

        self.logger.debug('Step %d (%d) - Reward %d',
            self.step_num, self.total_step_num, reward)

        return time_step.transition(
            observation, reward=reward, discount=self.std_discount)

    """ Transforming AIStateData to TF-Agent Observation """

    def _get_image_object_info(self, obj):
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
        client_x, client_y = get_rect_center(rect)
        x_grid, y_grid = self._client_point_to_grid_point(client_x, client_y)

        confidence = int(obj['confidence'] * 100) if obj['confidence'] is not None else 10

        return label_val, confidence, x_grid, y_grid

    def _get_image_object_observation_vec(self, obj):
        """Transform image_object from AIState to vector"""
        label_val, confidence, x_grid, y_grid = self._get_image_object_info(obj)
        return np.array((label_val, confidence, x_grid, y_grid), dtype=np.int32)

    def _ai_state_to_observation1(self, state):
        """Transform AIState to numpy array following observation_spec_1"""
        num_img_objs = len(state.image_objects)
        obj_vectors = []
        for i in range(self.num_observation_objects):
            vec = np.array((self.obj_name_int_vals['none'], 0, 0, 0), dtype=np.int32)
            if i < num_img_objs:
                obj = state.image_objects[i]
                vec = self._get_image_object_observation_vec(obj)
            obj_vectors.append(vec)

        step_mod = self.step_num % self.step_num_obs_mod
        step_num_vecs = [(step_mod, step_mod, step_mod, step_mod), ]
        return np.array(step_num_vecs + obj_vectors, dtype=np.int32)

    def _ai_state_to_observation2(self, state):
        """Transform AIState to numpy array following observation_spec_2"""

        # get zero-valued observation
        obs = np.zeros((self.grid_width, self.grid_height, 2), dtype=np.int32)

        # fill in image objects
        for obj in state.image_objects:
            label_val, confidence, x_grid, y_grid = self._get_image_object_info(obj)

            # insert if nothing there or we should overwrite anyway
            should_insert = obs[x_grid][y_grid][0] == 0 \
                or random.random() < self.os2_overwrite_prob
            if should_insert:
                obs[x_grid][y_grid][0] = label_val
                obs[x_grid][y_grid][1] = confidence

        return obs

    def ai_state_to_observation(self, state):
        """Transform AIState to numpy array following observation_spec"""
        if self.obs_spec_mode == 1:
            return self._ai_state_to_observation1(state)
        else:
            return self._ai_state_to_observation2(state)

    # def observation_to_ai_state(self, observation):
    #     # TODO: this is imperfect (money, stars, anything but image objects)
    #     # but do I need the reverse transformation?
    #
    #     image_objects = []
    #     for vec in observation[1:]:
    #         label_val, confidence_int, x_grid, y_grid = vec
    #         label = self.obj_int_val_names[label_val] if label_val in self.obj_int_val_names else 'none'
    #         confidence = float(confidence_int) / 100
    #         x, y = self._grid_point_to_client_point(x_grid, y_grid)
    #         w, h = (80, 80)
    #         obj = {'label': label, 'confidence': confidence, 'rect': Rect(x - w / 2, y - h / 2, w, h)}
    #         image_objects.append(obj)
    #
    #     return AIState(
    #         image_shape=(self.client_width, self.client_height, 3),
    #         image_objects=image_objects,
    #     )

    def get_cur_ai_state(self):
        return self.action_state_manager.get_cur_screen_state()

    def _get_current_tf_obs(self):
        ai_state = self.get_cur_ai_state()
        return self.ai_state_to_observation(ai_state)

    def _get_empty_tf_obs(self):
        empty_state = AIState()
        return self.ai_state_to_observation(empty_state)

    def _cleanup_current_step(self):
        pass

    """ Transforming Actions to and from TF-Agent matrices """

    def tf_action_to_ai_action(self, tf_action):
        if self.action_spec_mode == 1:
            return self._tf_action1_to_ai_action(tf_action)
        elif self.action_spec_mode == 2:
            return self._tf_action2_to_ai_action(tf_action)
        else:
            return self._tf_action3_to_ai_action(tf_action)

    def ai_action_to_tf_action(self, ai_action_tup):
        action, args = ai_action_tup
        if self.action_spec_mode == 1:
            return self._ai_action_to_tf_action1(action, args)
        elif self.action_spec_mode == 2:
            return self._ai_action_to_tf_action2(action, args)
        else:
            return self._ai_action_to_tf_action3(action, args)

    def _grid_point_to_client_point(self, x_grid, y_grid):
        x, y = (x_grid * self.client_width_factor, y_grid * self.client_height_factor)
        return int(x), int(y)

    def _get_tap_action(self, action_name, x_grid, y_grid):
        x, y = self._grid_point_to_client_point(x_grid, y_grid)
        ai_state = self.get_cur_ai_state()
        img_obj, obj_dist = ai_state.find_nearest_object(x, y, 60) if ai_state else (None, 0)

        action_data = get_object_action_data(img_obj) if img_obj else {
            'x': x,
            'y': y,
            'type': 'object',
            'object_type': 'unknown',
            'img_obj': {'confidence': 0.1}
        }
        return (action_name, action_data)

    def _get_swipe_action(self, action_name):
        return (action_name, {'distance': 400})

    def _tf_action1_to_ai_action(self, tf_action1):
        action_name, x_grid, y_grid = tf_action1[0:3]
        if action_name in [Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION]:
            return self._get_tap_action(action_name, x_grid, y_grid)
        elif action_name in [Action.SWIPE_LEFT, Action.SWIPE_RIGHT]:
            return self._get_swipe_action(action_name)
        elif action_name in [Action.PASS, Action.RESET]:
            # reset only is reset if x and y are also zero :)
            # prevents random policy / untrained deep q from too many resets
            return (action_name, {}) if x_grid == 0 and y_grid == 0 else (Action.PASS, {})
        else:
            return (Action.PASS, {})

    def _tf_action2_to_ai_action(self, tf_action2):
        action_int = int(tf_action2)

        # pass, reset
        if action_int <= Action.RESET:
            return (action_int, {})

        val = action_int - 2
        if val < self.total_as2_swipe_actions:
            name = Action.SWIPE_LEFT if val % 2 == 0 else Action.SWIPE_RIGHT
            return self._get_swipe_action(name)

        # convert single digit to coded action, x, y value (see above docs)
        val = action_int - 2 - self.total_as2_swipe_actions
        gw, midpoint = (self.grid_width, self.grid_area)
        action_name = Action.TAP_LOCATION \
            if val <= midpoint else Action.DOUBLE_TAP_LOCATION
        grid_val = val if val <= midpoint else val - midpoint
        y_grid = int(grid_val / gw)
        x_grid = grid_val % gw
        return self._get_tap_action(action_name, x_grid, y_grid)

    def _tf_action3_to_ai_action(self, tf_action3):
        action_int = int(tf_action3)

        # pass, reset
        if action_int <= Action.RESET:
            return (action_int, {})

        val = action_int - 2
        if val < self.total_as3_swipe_actions:
            name = Action.SWIPE_LEFT if val % 2 == 0 else Action.SWIPE_RIGHT
            return self._get_swipe_action(name)

        # convert single digit to coded action, x, y value (see above docs)
        grid_val = action_int - 2 - self.total_as3_swipe_actions
        action_name = Action.DOUBLE_TAP_LOCATION \
            if random.random() < self.as3_dtap_prob else Action.TAP_LOCATION
        y_grid = int(grid_val / self.grid_width)
        x_grid = grid_val % self.grid_width
        return self._get_tap_action(action_name, x_grid, y_grid)

    def _client_point_to_grid_point(self, x, y):
        x_grid = int(x / self.client_width_factor)
        y_grid = int(y / self.client_height_factor)
        return x_grid, y_grid

    def _get_ai_action_grid_point(self, action_val, args):
        hasxy = action_val in [Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION]
        x, y = [args[k] for k in ('x', 'y')] if hasxy else (0, 0)
        return self._client_point_to_grid_point(x, y)

    def _ai_action_to_tf_action1(self, action_val, args):
        x_grid, y_grid = self._get_ai_action_grid_point(action_val, args)
        return np.array((action_val, x_grid, y_grid), dtype=np.int32)

    def _ai_action_to_tf_action2(self, action_val, args):
        if action_val not in[Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION]:
            return action_val

        x_grid, y_grid = self._get_ai_action_grid_point(action_val, args)
        grid_val = (y_grid * self.grid_width) + x_grid
        val = (2 + self.total_as2_swipe_actions) + grid_val
        if action_val == Action.DOUBLE_TAP_LOCATION:
            val += self.grid_area
        return val

    def _ai_action_to_tf_action3(self, action_val, args):
        if action_val not in[Action.TAP_LOCATION, Action.DOUBLE_TAP_LOCATION]:
            return action_val

        x_grid, y_grid = self._get_ai_action_grid_point(action_val, args)
        grid_val = (y_grid * self.grid_width) + x_grid
        val = (2 + self.total_as3_swipe_actions) + grid_val
        return val

    def _take_ai_action(self, action, args):
        self.action_state_manager.attempt_action(action, args)
