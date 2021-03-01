""" Shared manager between old ai_env and tf_ai_env """

import json
import time
from kim_logs import get_kim_logger
from enums import Action
from ai_state_data import AIState
from ai_info_publisher import get_ai_info_publisher
from config import REDIS_HOST, REDIS_PORT, SWIPE_DURATION


class DeviceClientEnvActionStateManager(object):
    """ Uses a DeviceClient to handle actions and state management on a
    KK:Hollywood environment """

    def __init__(self, client, host=REDIS_HOST, port=REDIS_PORT):
        self.client = client
        self.logger = get_kim_logger('DeviceClientEnvActionStateManager')
        self.ai_info_publisher = get_ai_info_publisher(host, port)
        self.cur_screen_index = 0
        self.cur_screen_state = None

        # Setup Actions Map
        self.actions_map = {
            Action.RESET: self.perform_reset_action,
            Action.PASS: self.perform_pass_action,
            Action.SWIPE_LEFT: self.perform_swipe_left_action,
            Action.SWIPE_RIGHT: self.perform_swipe_right_action,
            Action.TAP_LOCATION: self.perform_tap_action,
            Action.DOUBLE_TAP_LOCATION: self.perform_double_tap_action,
        }

        # Redis to grab the screen state from the phone_image_stream process
        self.p = self.ai_info_publisher.r.pubsub(ignore_subscribe_messages=True)
        self.p.subscribe(**{
            'phone-image-states': self._handle_phone_image_states
        })
        self.p_thread = self.p.run_in_thread(sleep_time=0.001)

    def _handle_phone_image_states(self, message):
        if message['type'] != 'message':
            return

        data = json.loads(message['data'])
        if data:
            self.cur_screen_index = data['index']
            self.cur_screen_state = AIState.deserialize(data['state'])

    def get_cur_screen_state(self):
        state = self.cur_screen_state
        return state if state is not None else AIState()

    def perform_pass_action(self, args):
        time.sleep(0.5)

    def perform_reset_action(self, args):
        self.client.reset_game()

    def perform_swipe_left_action(self, args):
        distance = args['distance'] if 'distance' in args else 200
        self.client.send_drag_x_command(distance=-distance, duration=SWIPE_DURATION)

    def perform_swipe_right_action(self, args):
        distance = args['distance'] if 'distance' in args else 200
        self.client.send_drag_x_command(distance=distance, duration=SWIPE_DURATION)

    def perform_tap_action(self, args):
        x, y, type = [args[k] for k in ['x', 'y', 'type']]
        type = args['object_type'] if type == 'object' else type
        self.client.send_tap_command(x, y, type)

    def perform_double_tap_action(self, args):
        x, y, type = [args[k] for k in ['x', 'y', 'type']]
        type = args['object_type'] if type == 'object' else type
        self.client.send_double_tap_command(x, y, type)

    def attempt_action(self, action, args):
        if action in self.actions_map:
            self.ai_info_publisher.publish_action(action, args)
            self.actions_map[action](args)
        else:
            self.logger.debug('unrecognized action %s' % action)
