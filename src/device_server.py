""" DeviceServer class to communicate with DeviceManager by commands over network """

import asyncore
import socket
import signal
import sys
import traceback
from java.lang import Runtime

from kim_logs import get_kim_logger
from config import DEVICE_HOST, DEVICE_PORT
from device_manager import get_default_device_manager
from asyncchat_kim import AsyncchatKim, KimCommand
from util import floatarr, intarr, kill_process


class DeviceMessageHandler(AsyncchatKim):
    '''
    Allows socket-based commands to control a DeviceManager
    '''

    def __init__(self,
                 device_manager,
                 sock,
                 gc_memory_kill_limit=10000000,
                 gc_command_interval=20):
        AsyncchatKim.__init__(
            self,
            logger_name='DSMsgHandler',
            py2=True,
            sock=sock)
        self.device_manager = device_manager
        self.gc_memory_kill_limit = gc_memory_kill_limit
        self.gc_command_interval = gc_command_interval
        self.cmd_count = 0

        self.command_handlers = {
            KimCommand.SCREENSHOT: self._handle_screenshot,
            KimCommand.GET_PROCESS: self._handle_get_process,
            KimCommand.RESET: self._handle_reset,
            KimCommand.DRAG_X: self._handle_drag_x,
            KimCommand.TAP: self._handle_tap,
            KimCommand.DOUBLE_TAP: self._handle_double_tap,
        }

    def _clean_memory(self):
        """ in an attempt to make everything run better, we pre-emptively
        kill the device server whenever memory gets too low, and allow the
        process hub to restart it """
        runtime = Runtime.getRuntime()
        mem_pre = runtime.freeMemory()
        runtime.gc()
        mem_post = runtime.freeMemory()
        self.logger.debug("free memory PRE GC: %d || POST GC: %d" % (mem_pre, mem_post))
        if mem_post < self.gc_memory_kill_limit:
            self.logger.info("Killing device server due to low memory.")
            kill_process()

    def _handle_command(self, command_id, command, data):
        self.cmd_count += 1
        if self.cmd_count % self.gc_command_interval == 0:
            self._clean_memory()

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
        self.host = host
        self.port = port
        self.logger = get_kim_logger('DeviceServer')
        self.message_handlers = []

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.address = self.socket.getsockname()
        self.listen(1)

    def start(self):
        """ Starts the server for listening to commands """
        self.logger.debug('Starting Device Server at %s:%d ...', self.host, self.port)
        asyncore.loop()

    def handle_accept(self):
        '''Called when a client (like DeviceClient) connects to our socket'''

        self.logger.debug('Connected to a new client...')
        sock, _ = self.accept()
        handler = DeviceMessageHandler(device_manager=self.device_manager, sock=sock)
        self.message_handlers.append(handler)

    def handle_close(self):
        self.close()

    def graceful_exit(self):
        self.logger.info('Gracefully exiting...')
        self.close()


def get_default_device_server():
    """ Creates server with default port and ip and default device manager """
    manager = get_default_device_manager()
    server = DeviceServer(manager)
    return server


def main():
    """ Starts the default server if file is run as a script """

    server = get_default_device_server()

    def signal_handler(sig, frame):
        server.graceful_exit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    server.start()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        kill_process()

    sys.exit(0)
