""" DeviceServer class to communicate with DeviceManager by commands over network """

import logging
import sys
import redis
from config import REDIS_HOST, REDIS_PORT
import device_client
from device_manager import get_default_device_manager


class DeviceServer(object):
    '''
    Allows redis-based commands to control a DeviceManager
    '''

    def __init__(self, device_manager, host=REDIS_HOST, port=REDIS_PORT):
        self.device_manager = device_manager
        self.logger = logging.getLogger('DeviceServer')
        self.logger.debug('Starting Device Server...')

        self.r = redis.StrictRedis(
            host=host, port=port, db=0, decode_responses=True)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)
        self.p_thread = None

    def start(self):
        ''' starts pubsub to listen to commands '''
        self.p.subscribe(**{'device-commands': self._handle_command})
        self.p_thread = self.p.run_in_thread(sleep_time=0.001)

    def send_ack(self, command_id):
        ''' Sends ACK of completed command with given id to client '''
        self.logger.debug('Sending ACK for command id %s', command_id)
        msg = device_client.COMMAND_SEP.join(
            [command_id, device_client.COMMAND_ACK])
        self.r.publish('device-command-acks', msg)

    def _handle_command(self, message):
        if message['type'] != 'message':
            return

        parts = message['data'].split(device_client.COMMAND_SEP)
        command_id, command, data = parts[0], parts[1], parts[2:]

        if command == device_client.COMMAND_SCREENSHOT:
            self._handle_screenshot(data[0])
        elif command == device_client.COMMAND_RESET:
            self._handle_reset()
        elif command == device_client.COMMAND_DRAG_X:
            self._handle_drag_x(data[0], data[1])
        elif command == device_client.COMMAND_TAP:
            self._handle_tap(data[0], data[1])
        else:
            self.logger.error('Received unknown command: %s', command)

        self.send_ack(command_id)

    def _handle_screenshot(self, filename):
        self.logger.debug(
            'Handling screenshot command with filename: %s',
            filename)
        self.device_manager.save_screenshot(filename)

    def _handle_reset(self):
        self.logger.debug('Handling reset command')
        self.device_manager.reset_hollywood()

    def _handle_drag_x(self, distance, duration):
        self.logger.debug(
            'Handling Drag X Command with (distance, duration): (%d, %.1f)',
            distance,
            duration)
        self.device_manager.drag_delta(delta_x=distance, duration=duration)

    def _handle_tap(self, x, y):
        self.logger.debug('Handling Tap Command with (x, y): (%d, %d)', x, y)
        self.device_manager.tap(x, y)


def get_default_device_server():
    """ Creates server with default port and ip and default device manager """
    manager = get_default_device_manager()
    server = DeviceServer(manager)
    return server


def main():
    """ Starts the default server if file is run as a script """
    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s.%(msecs)03d:%(levelname)s:%(name)s:%(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

    server = get_default_device_server()
    server.start()


if __name__ == "__main__":
    main()
