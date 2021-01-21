"""
Contains KimEnv class for controlling the game via the learning algorithm.
"""

from kim_logs import get_kim_logger
from ai_actions import Action
from ai_state import AIStateProcessor
from env_action_state_manager import DeviceClientEnvActionStateManager
from config import REDIS_HOST, REDIS_PORT, IMG_CONFIG_STUDIOBLU


class KimEnv(object):
    """Abstract class which Controls a device running KK:Hollywood via a minimal interface.
    Modeled after the OpenAI Env API.
    """

    def __init__(self):
        self.step_num = 0
        self.logger = get_kim_logger('KimEnv')

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


class DeviceClientKimEnv(KimEnv):
    """Implements KimEnv with a DeviceClient"""

    def __init__(self, client, host=REDIS_HOST, port=REDIS_PORT):
        KimEnv.__init__(self)
        self.action_state_manager = DeviceClientEnvActionStateManager(client, host, port)
        self.client = client

    def _do_reset(self):
        self.client.reset_game()

    def _get_state(self):
        return self.action_state_manager.cur_screen_state

    def _take_action(self, action, args):
        self.action_state_manager.attempt_action(action, args)


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
