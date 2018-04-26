""" DeviceServer class to communicate with DeviceManager by commands over network """

import asynchat
import asyncore
import logging
import socket
import sys
import device_client
from device_manager import get_default_device_manager

class DeviceMessageHandler(asynchat.async_chat):
    '''
    Allows socket-based commands to control a DeviceManager
    '''

    def __init__(self, device_manager, sock):
        asynchat.async_chat.__init__(self, sock)
        self.device_manager = device_manager
        self.logger = logging.getLogger('DeviceMessageHandler')

        self.set_terminator('\n')
        self.buffer = []

    def collect_incoming_data(self, data):
        '''Add data to buffer until we see \n'''
        self.buffer.append(data)

    def found_terminator(self):
        '''We have received a full message'''
        msg = ''.join(self.buffer)
        self.logger.debug('received message: %s', msg)
        self.buffer = []
        self._handle_command(msg)

    def send_ack(self, command_id):
        ''' Sends ACK of completed command with given id to client '''
        self.logger.debug('Sending ACK for command id %s', command_id)
        msg = device_client.COMMAND_SEP.join([device_client.COMMAND_ACK, command_id]) + '\n'
        self.push(msg.encode())

    def _handle_command(self, msg):
        parts = msg.split(device_client.COMMAND_SEP)
        command_id = parts[0]
        command = parts[1]
        data = parts[2:]

        if command == device_client.COMMAND_SCREENSHOT:
            self._handle_screenshot(data[0])
        elif command == device_client.COMMAND_RESET:
            self._handle_reset()
        else:
            self.logger.error('Received unknown command: %s', command)

        self.send_ack(command_id)

    def _handle_screenshot(self, filename):
        self.logger.debug('Handling screenshot command with filename: %s', filename)

        self.device_manager.save_screenshot(filename)

    def _handle_reset(self):
        self.logger.debug('Handling reset command')

        self.device_manager.reset_hollywood()

class DeviceServer(asyncore.dispatcher):
    '''
    Manages the creation of DeviceMessageHandlers for every incoming Socket client
    '''

    def __init__(self, device_manager, ip=device_client.DEFAULT_DEVICE_IP, port=device_client.DEFAULT_DEVICE_PORT):
        asyncore.dispatcher.__init__(self)
        self.device_manager = device_manager
        self.logger = logging.getLogger('DeviceServer')

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((ip, port))
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
        DeviceMessageHandler(device_manager=self.device_manager, sock=client_info[0])

    def handle_close(self):
        self.close()

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
