"""
Contains KimEnv class for controlling the game via the learning algorithm.
"""

import logging
import os
from ai_actions import Action
from ai_state import AIStateProcessor, IMG_CONFIG_STUDIOBLU

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

    def step(self, action=Action.PASS):
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
        actions_map = {
            Action.PASS: self._perform_pass_action,
            Action.SWIPE_LEFT: self._perform_swipe_left_action,
            Action.SWIPE_RIGHT: self._perform_swipe_right_action
        }
        actions_map[action]()

        # Get new state
        self.logger.debug('Getting state for Step #%d', self.step_num)
        next_state = self._get_state()
        self.logger.debug('State for Step #%d: %s', self.step_num, next_state)

        reward = next_state.get_reward()
        done = False
        info = {}

        return next_state, reward, done, info

    def _cleanup_current_step(self):
        pass

    def _do_reset(self):
        pass

    def _get_state(self):
        pass

    def _perform_pass_action(self):
        pass

    def _perform_swipe_left_action(self):
        pass

    def _perform_swipe_right_action(self):
        pass


class DeviceClientKimEnv(KimEnv):
    """Implements KimEnv with a DeviceClient"""
    def __init__(self, client):
        KimEnv.__init__(self)
        self.client = client
        self.state_processor = AIStateProcessor()

    def _do_reset(self):
        self.client.send_reset_command()

    def _cleanup_current_step(self):
        if self.step_num == 0:
            return

        filename = self._cur_filename()
        self.logger.debug('Removing used file: %s', filename)
        os.remove(filename)

    def _get_state(self):
        filename = self._cur_filename()
        self.client.send_screenshot_command(filename)
        state = self.state_processor.process_from_file(None, filename)
        return state

    def _cur_filename(self):
        return 'screen_%d.png' % self.step_num

    def _perform_swipe_left_action(self):
        self.client.send_drag_x_command(distance=-100)

    def _perform_perform_swipe_right_action(self):
        self.client.send_drag_x_command(distance=100)

class ScreenshotKimEnv(KimEnv):
    """Implements KimEnv with a static screenshot"""
    def __init__(self, screenshot_filename="src/img/blu_screenshot_1.png", image_config=IMG_CONFIG_STUDIOBLU):
        KimEnv.__init__(self)
        self.screenshot_filename = screenshot_filename
        self.state_processor = AIStateProcessor(image_config=image_config)

    def _get_state(self):
        state = self.state_processor.process_from_file(None, self.screenshot_filename)
        return state
