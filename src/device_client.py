""" Connects to a DeviceServer over network to control a DeviceManager, somewhere """

import asyncore
import time
import socket
import threading
from asyncchat_kim import AsyncchatKim, KimCommand
from config import CURRENT_PHONE_GAME_RECT, VYSOR_CAP_AREA
from window import setup_vysor_window


class DeviceClient(AsyncchatKim):
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer.

    Also performs the *extremely desirable* task of translating points from
    image read on screen to point on device (we use a smaller image for reading)
    for performance reasons.
    '''

    def __init__(self,
                 phone_game_rect=CURRENT_PHONE_GAME_RECT,
                 img_rect=VYSOR_CAP_AREA):
        AsyncchatKim.__init__(self, py2=False, logger_name='DeviceClient')
        self.phone_game_rect = phone_game_rect
        self.img_rect = img_rect

    def start(self, max_attempts=5):
        """ Connects the client to a server """
        self.logger.debug('Connecting to %s:%d', self.host, self.port)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))

        attempt_num = 0
        while not self.connected and attempt_num < max_attempts:
            if attempt_num > 1:
                self.logger.debug('Re-connect attempt #{}/{}'.format(attempt_num, max_attempts - 1))
                time.sleep(1)
            try:
                self.connect((self.host, self.port))
            except ConnectionRefusedError:
                self.logger.debug('Connection Refused')
            attempt_num += 1

        if not self.connected:
            raise ConnectionRefusedError('Device Client Unable to connect')

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

        data = self.get_command_res_data(command_id)
        return data

    def _send_command(self, *args):
        command_id = str(self.command_id)
        AsyncchatKim._send_command(self, *args)

        # Wait for ack for "consistency!!"
        res_data = self._wait_for_ack(command_id)
        return res_data

    def send_screenshot_command(self, filename):
        """ Sends a command to save screenshot to given filename """
        self._send_command(KimCommand.SCREENSHOT, filename)

    def get_cur_process_command(self):
        """ Sends a command to get current process from monkey device """
        name = self._send_command(KimCommand.GET_PROCESS)
        return name[0] if name is not None and len(name) > 0 else None

    def reset_game(self):
        """ Sends a command to restart the game """
        self._send_command(KimCommand.RESET)
        setup_vysor_window()
        time.sleep(1)

    def _img_point_to_device_point(self, img_point):
        x, y = img_point
        _, _, w1, h1 = self.img_rect
        x2, y2, w2, h2 = self.phone_game_rect
        nx = (w2 / float(w1)) * x + x2
        ny = (h2 / float(h1)) * y + y2
        return (int(nx), int(ny))

    def send_drag_x_command(self, distance=100, duration=1):
        """ Sends a command to swipe left for given duration / distance """
        self._send_command(KimCommand.DRAG_X, distance, duration)

    def send_tap_command(self, x, y, type):
        ''' Sends command to tap device at given location '''
        nx, ny = self._img_point_to_device_point((x, y))
        self._send_command(KimCommand.TAP, nx, ny, type)

    def send_double_tap_command(self, x, y, type):
        ''' Sends command to tap device at given location '''
        nx, ny = self._img_point_to_device_point((x, y))
        self._send_command(KimCommand.DOUBLE_TAP, nx, ny, type)
