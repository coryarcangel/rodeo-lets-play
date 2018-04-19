""" Connects to a DeviceServer over network to control a DeviceManager, somewhere """

import asynchat
import asyncore
import logging
import socket
import threading

# Constants
DEFAULT_DEVICE_IP = '127.0.0.1'
DEFAULT_DEVICE_PORT = 5005
COMMAND_SEP = '|'
COMMAND_SCREENSHOT = 'SCREENSHOT'
COMMAND_RESET = 'RESET'
COMMAND_ACK = 'ACK'

class DeviceClient(asynchat.async_chat):
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer
    '''

    def __init__(self, device_ip=DEFAULT_DEVICE_IP, port=DEFAULT_DEVICE_PORT):
        asynchat.async_chat.__init__(self)
        self.device_ip = device_ip
        self.port = port
        self.logger = logging.getLogger('DeviceClient')
        self.command_id = 0
        self.command_ack_map = {}
        self.buffer = []
        self.comm = None

    def start(self):
        """ Connects the client to a server """
        self.logger.debug('Connecting to %s:%d', self.device_ip, self.port)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.device_ip, self.port))
        self.set_terminator('\n')
        self.buffer = []

        self.comm = threading.Thread(target=asyncore.loop)
        self.comm.daemon = True
        self.comm.start()

    def collect_incoming_data(self, data):
        self.buffer.append(data.decode())

    def found_terminator(self):
        msg = ''.join(self.buffer)
        self.logger.debug('received message: %s', msg)
        self.buffer = []
        self._handle_message(msg)

    def _handle_message(self, msg):
        # Handle an ACK message
        parts = msg.split(COMMAND_SEP)
        if parts[0] == COMMAND_ACK:
            command_id = parts[1]
            self.command_ack_map[command_id] = True

    def _has_received_cmd_ack(self, command_id):
        return command_id in self.command_ack_map

    def _send_command(self, *args):
        # grab current command id and send message
        command_id = str(self.command_id)
        msg = COMMAND_SEP.join((command_id,) + args) + '\n'
        self.logger.debug('Sending message: %s', msg.rstrip())
        self.push(msg.encode('utf-8'))

        # increment id for next command
        self.command_id += 1

        # wait for ACK
        while not self._has_received_cmd_ack(command_id):
            pass

    def send_screenshot_command(self, filename):
        """ Sends a command to save screenshot to given filename """
        self._send_command(COMMAND_SCREENSHOT, filename)

    def send_reset_command(self):
        """ Sends a command to restart the game """
        self._send_command(COMMAND_RESET)

def get_default_device_client():
    """ Returns DeviceClient connected to default host and port """
    return DeviceClient()
