""" Connects to a DeviceServer over network to control a DeviceManager, somewhere """

import asyncore
import time
import socket
import threading
from asyncchat_kim import AsyncchatKim, KimCommand

class DeviceClient(AsyncchatKim):
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer
    '''

    def __init__(self):
        AsyncchatKim.__init__(self, py2=False, logger_name='DeviceClient')

    def start(self):
        """ Connects the client to a server """
        self.logger.debug('Connecting to %s:%d', self.host, self.port)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))

        self.comm = threading.Thread(target=asyncore.loop)
        self.comm.daemon = True
        self.comm.start()

    def _has_received_cmd_ack(self, command_id):
        return command_id in self.command_ack_map

    def _wait_for_ack(self, command_id):
        while not self._has_received_cmd_ack(command_id):
            time.sleep(0.001)

    def _send_command(self, *args):
        command_id = str(self.command_id)
        AsyncchatKim._send_command(self, *args)

        # Wait for ack for "consistency!!"
        self._wait_for_ack(command_id)

    def send_screenshot_command(self, filename):
        """ Sends a command to save screenshot to given filename """
        self._send_command(KimCommand.SCREENSHOT, filename)

    def send_reset_command(self):
        """ Sends a command to restart the game """
        self._send_command(KimCommand.RESET)

    def send_drag_x_command(self, distance=100, duration=0.5):
        """ Sends a command to swipe left for given duration / distance """
        self._send_command(KimCommand.DRAG_X, distance, duration)

    def send_tap_command(self, x, y):
        ''' Sends command to tap device at given location '''
        self._send_command(KimCommand.TAP, x, y)


def get_default_device_client():
    """ Returns DeviceClient connected to default host and port """
    return DeviceClient()
