""" Connects to a DeviceServer over network to control a DeviceManager, somewhere """

import asyncore
import time
import socket
import threading
from asyncchat_kim import AsyncchatKim, KimCommand
from config import CURRENT_PHONE_GAME_RECT, VYSOR_CAP_AREA
from config import SAFEGUARD_MENU_RECTS, SAFEGUARD_MENU_CLICKS_DEFAULT
from util import is_in_rect, convert_point_between_rects
from window_setup import setup_vysor_window
from enums import Action
from ai_info_publisher import get_ai_info_publisher


class DeviceClient(AsyncchatKim):
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer.

    Also performs the *extremely desirable* task of translating points from
    image read on screen to point on device (we use a smaller image for reading)
    for performance reasons.
    '''

    def __init__(self,
                 phone_game_rect=CURRENT_PHONE_GAME_RECT,
                 img_rect=VYSOR_CAP_AREA,
                 safeguard_menu_clicks=SAFEGUARD_MENU_CLICKS_DEFAULT,
                 on_connection_fail=None,
                 superlong_timeout_seconds=60,
                 on_superlong_timeout=None):
        AsyncchatKim.__init__(self, py2=False, logger_name='DeviceClient')
        self.phone_game_rect = phone_game_rect
        self.img_rect = img_rect
        self.safeguard_menu_clicks = safeguard_menu_clicks
        self.on_connection_fail = on_connection_fail
        self.superlong_timeout_seconds = superlong_timeout_seconds
        self.on_superlong_timeout = on_superlong_timeout
        self.ai_info_publisher = get_ai_info_publisher()
        self.is_closed = False

    def start(self, max_attempts=5):
        """ Connects the client to a server """
        self.logger.debug('Connecting to %s:%d', self.host, self.port)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))

        attempt_num = 0
        while not self.connected and attempt_num < max_attempts:
            if attempt_num > 1:
                self.logger.debug('Re-connect attempt #{}/{}'.format(attempt_num, max_attempts - 1))
                time.sleep(2)
            try:
                self.connect((self.host, self.port))
            except ConnectionRefusedError:
                self.logger.debug('Connection Refused')
            attempt_num += 1

        if not self.connected:
            if self.on_connection_fail:
                self.on_connection_fail()
            raise ConnectionRefusedError('Device Client Unable to connect')

        self.is_closed = False
        if not self.comm:
            self.comm = threading.Thread(target=asyncore.loop)
            self.comm.daemon = True
            self.comm.start()

    def handle_close(self):
        if not self.is_closed:
            self.logger.debug('Disconnected from %s:%d', self.host, self.port)
            self.logger.debug('Will Attempt Connect in 20 seconds')
            self.close()
            self.is_closed = True
            time.sleep(20)
            self.start()
        pass

    def _wait_for_ack(self, command_id, timeout=10):
        now = time.time()
        while not self._has_received_cmd_ack(command_id):
            time.sleep(0.001)
            elapsed = time.time() - now
            if self.connected and elapsed >= timeout:
                self.logger.debug(
                    'Timeout receving ACK for command %s' %
                    command_id)
                break
            elif elapsed >= self.superlong_timeout_seconds:
                if self.on_superlong_timeout:
                    self.on_superlong_timeout()
                break

        data = self.get_command_res_data(command_id)
        return data

    def _send_command(self, *args):
        command_id = AsyncchatKim._send_command(self, *args)

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
        self.ai_info_publisher.publish_action(Action.RESET, {})
        self._send_command(KimCommand.RESET)
        setup_vysor_window()
        time.sleep(1)

    def _img_point_to_device_point(self, img_point):
        return convert_point_between_rects(img_point, self.img_rect, self.phone_game_rect)

    def _can_tap_device_point(self, x, y):
        if not self.safeguard_menu_clicks:
            return True

        for rect in SAFEGUARD_MENU_RECTS:
            if is_in_rect((x, y), rect):
                self.logger.info('Safeguarded point ({}, {})'.format(x, y))
                return False

        return True

    def send_drag_x_command(self, distance=100, duration=1):
        """ Sends a command to swipe left for given duration / distance """
        self._send_command(KimCommand.DRAG_X, distance, duration)

    def send_tap_command(self, x, y, type):
        ''' Sends command to tap device at given location '''
        nx, ny = self._img_point_to_device_point((x, y))
        if self._can_tap_device_point(nx, ny):
            self._send_command(KimCommand.TAP, nx, ny, type)

    def send_double_tap_command(self, x, y, type):
        ''' Sends command to tap device at given location '''
        nx, ny = self._img_point_to_device_point((x, y))
        if self._can_tap_device_point(nx, ny):
            self._send_command(KimCommand.DOUBLE_TAP, nx, ny, type)
