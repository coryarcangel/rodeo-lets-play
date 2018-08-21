""" Connects to a DeviceServer over network to control a DeviceManager, somewhere """

import json
import logging
import time
import redis
from config import REDIS_HOST, REDIS_PORT
from ai_state import AIState

# Constants
COMMAND_SEP = '|'
COMMAND_SCREENSHOT = 'SCREENSHOT'
COMMAND_RESET = 'RESET'
COMMAND_DRAG_X = 'DRAG'
COMMAND_TAP = 'TAP'
COMMAND_ACK = 'ACK'

class DeviceClient(object):
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer
    '''

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.host = host
        self.port = port
        self.logger = logging.getLogger('DeviceClient')

        self.command_id = 0
        self.command_ack_map = {}

        self.cur_screen_index = 0
        self.cur_screen_state = None

        self.logger.debug('Connecting to %s:%d', host, port)
        self.r = redis.StrictRedis(host=host, port=port, db=0, decode_responses=True)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)
        self.p_thread = None

    def start(self):
        ''' starts pubsub to listen to commands '''
        self.p.subscribe(**{
            'device-commands': self._handle_command,
            'phone-image-states': self._handle_phone_yolo
        })
        self.p_thread = self.p.run_in_thread(sleep_time=0.001)

    def _has_ack(self, cmd_id):
        return cmd_id in self.command_ack_map

    def _send_command(self, *args):
        # grab current command id and send message
        command_id = str(self.command_id)
        msg = COMMAND_SEP.join((command_id,) + args)
        self.logger.debug('Sending message: %s', msg)
        self.r.publish('device-commands', msg)

        # increment id for next command
        self.command_id += 1

        # Wait for ack for "consistency!!"
        while not self._has_ack(command_id):
            time.sleep(0.001)

    def _handle_command(self, message):
        if message['type'] != 'message':
            return

        command_id, command = message['data'].split(COMMAND_SEP)
        if command != COMMAND_ACK:
            return

        self.command_ack_map[command_id] = True

    def _handle_phone_yolo(self, message):
        if message['type'] != 'message':
            return

        data = json.loads(message)
        self.cur_screen_index = data['index']
        self.cur_screen_state = AIState.deserialize(data['state'])

    def send_screenshot_command(self, filename):
        """ Sends a command to save screenshot to given filename """
        self._send_command(COMMAND_SCREENSHOT, filename)

    def send_reset_command(self):
        """ Sends a command to restart the game """
        self._send_command(COMMAND_RESET)

    def send_drag_x_command(self, distance=100, duration=0.5):
        """ Sends a command to swipe left for given duration / distance """
        self._send_command(COMMAND_DRAG_X, distance, duration)

    def send_tap_command(self, x, y): #pylint: disable=C0103
        ''' Sends command to tap device at given location '''
        self._send_command(COMMAND_TAP, x, y)

def get_default_device_client():
    """ Returns DeviceClient connected to default host and port """
    return DeviceClient()
