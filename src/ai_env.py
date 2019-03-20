"""
Contains KimEnv class for controlling the game via the learning algorithm.
"""

import logging
import json
import redis
from time import time
from ai_actions import Action
from ai_state import AIState, AIStateProcessor
from config import REDIS_HOST, REDIS_PORT, IMG_CONFIG_STUDIOBLU


class KimEnv(object):
    """Abstract class which Controls a device running KK:Hollywood via a minimal interface.
    Modeled after the OpenAI Env API.
    """

    def __init__(self):
        self.step_num = 0
        self.logger = logging.getLogger('KimEnv')

    def reset(self):
        """Resets the state of the environment and returns an initial observation.

        Returns:
            Initial AIState object
        """
        self._cleanup_current_step()
        self._do_reset()
        self.logger.debug('Reset AI Environment')

        state = self._get_state()
        return state

    def step(self, action=Action.PASS, action_args=None):
        """Performs given action on environment, attempting to run 1 timestep. When end of
        episode is reached, you are responsible for calling `reset()`
        to reset this environment's state.
        Accepts an action and returns a tuple (observation, reward, done, info).
        Args:
            action (object): an action provided by the environment
        Returns:
            observation (np array): agent's observation of the current environment
            reward (float) : amount of reward returned after previous action
            done (boolean): whether the episode has ended, in which case further step() calls will return undefined results
            info (dict): contains auxiliary diagnostic information (helpful for debugging, and sometimes learning)
        """

        self._cleanup_current_step()

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

    def _cleanup_current_step(self):
        pass

    def _do_reset(self):
        pass

    def _get_state(self):
        pass

    def _perform_pass_action(self, args):
        pass


class DeviceClientKimEnv(KimEnv):
    """Implements KimEnv with a DeviceClient"""

    def __init__(self, client, host=REDIS_HOST, port=REDIS_PORT):
        KimEnv.__init__(self)
        self.client = client

        self.cur_screen_index = 0
        self.cur_screen_state = None

        # Setup Actions Map
        self.actions_map = {
            Action.PASS: self._perform_pass_action,
            Action.SWIPE_LEFT: self._perform_swipe_left_action,
            Action.SWIPE_RIGHT: self._perform_swipe_right_action,
            Action.TAP_LOCATION: self._perform_tap_action
        }

        # Redis to grab the screen state from the phone_image_stream process
        self.logger.debug('Connecting to %s:%d', host, port)
        self.r = redis.StrictRedis(
            host=host, port=port, db=0, decode_responses=True)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)

        self.p.subscribe(**{
            'phone-image-states': self._handle_phone_yolo
        })
        self.p_thread = self.p.run_in_thread(sleep_time=0.001)

    def _do_reset(self):
        self.client.send_reset_command()

    def _get_state(self):
        return self.cur_screen_state

    def _handle_phone_yolo(self, message):
        if message['type'] != 'message':
            return

        data = json.loads(message['data'])
        if data:
            self.cur_screen_index = data['index']
            self.cur_screen_state = AIState.deserialize(data['state'])

    def _publish_action(self, action, args):
        if action == Action.TAP_LOCATION:
            self.r.publish('ai-phone-touches', json.dumps({
                'type': 'tap',
                'time': time(),
                'args': args
            }))

    def _take_action(self, action, args):
        if (action in self.actions_map):
            self._publish_action(action, args)
            self.actions_map[action](args)
        else:
            self.logger.debug('unrecognized action %s' % action)

    def _perform_swipe_left_action(self, args):
        distance = args['distance'] if 'distance' in args else 200
        self.client.send_drag_x_command(distance=-distance)

    def _perform_swipe_right_action(self, args):
        distance = args['distance'] if 'distance' in args else 200
        self.client.send_drag_x_command(distance=distance)

    def _perform_tap_action(self, args):
        x, y, type = [args[k] for k in ['x', 'y', 'type']]
        type = args['object_type'] if type == 'object' else type
        self.client.send_tap_command(x, y, type)


class ScreenshotKimEnv(KimEnv):
    """Implements KimEnv with a static screenshot"""

    def __init__(self, screenshot_filename="src/img/blu_screenshot_1.png",
                 image_config=IMG_CONFIG_STUDIOBLU):
        KimEnv.__init__(self)
        self.screenshot_filename = screenshot_filename
        self.state_processor = AIStateProcessor(image_config=image_config)

    def _get_state(self):
        state = self.state_processor.process_from_file(
            None, self.screenshot_filename)
        return state
