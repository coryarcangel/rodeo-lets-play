""" DeviceServer class to communicate with DeviceManager by commands over network """

import asyncore
import os
import socket
import signal
import sys
import traceback
from kim_logs import get_kim_logger
from config import DEVICE_HOST, DEVICE_PORT
from device_manager import get_default_device_manager
from asyncchat_kim import AsyncchatKim, KimCommand
from util import floatarr, intarr


class DeviceMessageHandler(AsyncchatKim):
    '''
    Allows socket-based commands to control a DeviceManager
    '''

    def __init__(self, device_manager, sock):
        AsyncchatKim.__init__(
            self,
            logger_name='DSMsgHandler',
            py2=True,
            sock=sock)
        self.device_manager = device_manager

        self.command_handlers = {
            KimCommand.SCREENSHOT: self._handle_screenshot,
            KimCommand.GET_PROCESS: self._handle_get_process,
            KimCommand.RESET: self._handle_reset,
            KimCommand.DRAG_X: self._handle_drag_x,
            KimCommand.TAP: self._handle_tap,
            KimCommand.DOUBLE_TAP: self._handle_double_tap,
        }

    def _handle_command(self, command_id, command, data):
        if command in self.command_handlers:
            res_data = None
            try:
                res_data = self.command_handlers[command](data)
            except TypeError, e:
                self.logger.error(
                    'TypeError handling command (%s, %s, %s): %s' %
                    (command_id, command, data, e))
            except Exception, e:
                self.logger.error(
                    'Unknown error handling command (%s, %s, %s): %s' %
                    (command_id, command, data, e))
        else:
            self.logger.error('Received unknown command: %s', command)

        self.send_ack(command_id, res_data)

    def _handle_screenshot(self, data):
        filename = data[0]
        self.logger.debug(
            'Handling screenshot command with filename: %s',
            filename)
        self.device_manager.save_screenshot(filename)

    def _handle_get_process(self, data):
        self.logger.debug('Handling get_process command')
        return self.device_manager.get_cur_app_name()

    def _handle_reset(self, data):
        self.logger.debug('Handling reset command')
        self.device_manager.reset_hollywood()

    def _handle_drag_x(self, data):
        distance, duration = floatarr(data)
        self.logger.debug(
            'Handling Drag X Command with (distance, duration): (%d, %.1f)',
            distance,
            duration)
        self.device_manager.drag_delta(delta_x=distance, duration=duration)

    def _handle_tap(self, data):
        x, y = intarr(data[0:2])
        type = data[2]
        self.logger.debug(
            'Handling Tap Command with (x, y, type): (%d, %d, %s)',
            x,
            y,
            type)
        self.device_manager.tap(x, y)

    def _handle_double_tap(self, data):
        x, y = intarr(data[0:2])
        type = data[2]
        self.logger.debug(
            'Handling Double Tap Command with (x, y, type): (%d, %d, %s)',
            x,
            y,
            type)
        self.device_manager.double_tap(x, y)


class DeviceServer(asyncore.dispatcher):
    '''
    Manages the creation of DeviceMessageHandlers for every incoming Socket client
    '''

    def __init__(self, device_manager, host=DEVICE_HOST, port=DEVICE_PORT):
        asyncore.dispatcher.__init__(self)
        self.device_manager = device_manager
        self.logger = get_kim_logger('DeviceServer')

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((DEVICE_HOST, port))
        self.address = self.socket.getsockname()
        self.listen(1)

    def start(self):
        """ Starts the server for listening to commands """
        self.logger.debug('Starting Device Server...')
        asyncore.loop()

    def handle_accept(self):
        '''Called when a client (like DeviceClient) connects to our socket'''

        self.logger.debug('Connected to a new client...')
        client_info = self.accept()
        DeviceMessageHandler(
            device_manager=self.device_manager,
            sock=client_info[0])

    def handle_close(self):
        self.close()


def get_default_device_server():
    """ Creates server with default port and ip and default device manager """
    manager = get_default_device_manager()
    server = DeviceServer(manager)
    return server


def main():
    """ Starts the default server if file is run as a script """
    server = get_default_device_server()
    server.start()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGKILL)

    sys.exit(0)
