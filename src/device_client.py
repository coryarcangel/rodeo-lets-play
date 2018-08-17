""" Connects to a DeviceServer over network to control a DeviceManager, somewhere """

import logging
import redis
from config import REDIS_HOST, REDIS_PORT

# Constants
COMMAND_SEP = '|'
COMMAND_SCREENSHOT = 'SCREENSHOT'
COMMAND_RESET = 'RESET'
COMMAND_DRAG_X = 'DRAG'
COMMAND_TAP = 'TAP'
COMMAND_ACK = 'ACK'

class DeviceClient():
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer
    '''

    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.host = host
        self.port = port
        self.logger = logging.getLogger('DeviceClient')
        self.command_id = 0

        self.logger.debug('Connecting to %s:%d', host, port)
        self.r = redis.StrictRedis(host=host, port=port, db=0, decode_responses=True)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)

    def _send_command(self, *args):
        # grab current command id and send message
        command_id = str(self.command_id)
        msg = COMMAND_SEP.join((command_id,) + args)
        self.logger.debug('Sending message: %s', msg)
        self.r.publish('device-commands', msg)

        # increment id for next command
        self.command_id += 1

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
