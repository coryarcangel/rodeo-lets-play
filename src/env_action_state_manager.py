""" Shared manager between old ai_env and tf_ai_env """

import json
import redis
from time import time
from kim_logs import get_kim_logger
from ai_actions import Action
from ai_state_data import AIState
from config import REDIS_HOST, REDIS_PORT


class DeviceClientEnvActionStateManager(object):
    """ Uses a DeviceClient to handle actions and state management on a
    KK:Hollywood environment """

    def __init__(self, client, host=REDIS_HOST, port=REDIS_PORT):
        self.client = client
        self.logger = get_kim_logger('DeviceClientEnvActionStateManager')

        self.cur_screen_index = 0
        self.cur_screen_state = None

        # Setup Actions Map
        self.actions_map = {
            Action.PASS: self.perform_pass_action,
            Action.SWIPE_LEFT: self.perform_swipe_left_action,
            Action.SWIPE_RIGHT: self.perform_swipe_right_action,
            Action.TAP_LOCATION: self.perform_tap_action,
            Action.DOUBLE_TAP_LOCATION: self.perform_double_tap_action,
        }

        # Redis to grab the screen state from the phone_image_stream process
        self.logger.debug('Connecting to %s:%d', host, port)
        self.r = redis.StrictRedis(
            host=host, port=port, db=0, decode_responses=True)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)

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

    def publish_data(self, channel, data):
        self.r.publish(channel, json.dumps(data))

    def publish_action(self, action, args):
        ad = None
        if action == Action.TAP_LOCATION:
            ad = {'type': 'tap', 'time': time(), 'args': args}
        elif action == Action.DOUBLE_TAP_LOCATION:
            ad = {'type': 'double_tap', 'time': time(), 'args': args}
        elif action == Action.SWIPE_LEFT or action == Action.SWIPE_RIGHT:
            ad = {'type': 'swipe', 'time': time(), 'args': args}
        elif action == Action.PASS:
            ad = {'type': 'pass', 'time': time(), 'args': args}
        if ad:
            self.publish_data('ai-phone-touches', ad)

    def perform_pass_action(self, args):
        pass

    def perform_swipe_left_action(self, args):
        distance = args['distance'] if 'distance' in args else 200
        self.client.send_drag_x_command(distance=-distance)

    def perform_swipe_right_action(self, args):
        distance = args['distance'] if 'distance' in args else 200
        self.client.send_drag_x_command(distance=distance)

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
            self.publish_action(action, args)
            self.actions_map[action](args)
        else:
            self.logger.debug('unrecognized action %s' % action)
