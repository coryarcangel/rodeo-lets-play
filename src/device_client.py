""" Connects to a DeviceServer over network to control a DeviceManager, somewhere """

import asyncore
import time
import socket
import threading
from asyncchat_kim import AsyncchatKim, KimCommand


class DeviceClient(AsyncchatKim):
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer.

    Also performs the *extremely desirable* task of translating points from
    image read on screen to point on device (we use a smaller image for reading)
    for performance reasons.
    '''

    def __init__(self, phone_rect, img_rect):
        AsyncchatKim.__init__(self, py2=False, logger_name='DeviceClient')
        self.phone_rect = phone_rect
        self.img_rect = img_rect

    def start(self):
        """ Connects the client to a server """
        self.logger.debug('Connecting to %s:%d', self.host, self.port)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))

        self.comm = threading.Thread(target=asyncore.loop)
        self.comm.daemon = True
        self.comm.start()

    def _wait_for_ack(self, command_id, timeout=10):
        now = time.time()
        while not self._has_received_cmd_ack(command_id):
            time.sleep(0.001)
            if time.time() - now >= timeout:
                self.logger.debug(
                    'Timeout receving ACK for command %s' %
                    command_id)
                break

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

    def _img_point_to_device_point(self, img_point):
        x, y = img_point
        x1, y1, w1, h1 = self.img_rect
        x2, y2, w2, h2 = self.phone_rect
        nx = ((x - x1) / w1) * w2 + x2
        ny = ((y - y1) / h1) * h2 + y2
        return (int(nx), int(ny))

    def send_drag_x_command(self, distance=100, duration=1):
        """ Sends a command to swipe left for given duration / distance """
        self._send_command(KimCommand.DRAG_X, distance, duration)

    def send_tap_command(self, x, y, type):
        ''' Sends command to tap device at given location '''
        nx, ny = self._img_point_to_device_point((x, y))
        self._send_command(KimCommand.TAP, nx, ny, type)
