import asynchat
import asyncore
import logging
import socket
import threading

# Constants
DefaultCommunicationIP = '127.0.0.1'
DefaultCommunicationPort = 5005
CommandSep = '|'
CommandScreenshot = 'SCREENSHOT'
CommandAck = 'ACK'

class DeviceClient(asynchat.async_chat):
    '''
    Allows any python process (like ai.py) to send commands to a DeviceServer
    '''
    def __init__(self, ip = DefaultCommunicationIP, port = DefaultCommunicationPort):
        asynchat.async_chat.__init__(self)
        self.ip = ip
        self.port = port
        self.logger = logging.getLogger('DeviceClient')
        self.command_id = 0
        self.command_ack_map = {}

    def start(self):
        self.logger.debug('Connecting to %s:%d', self.ip, self.port)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.ip, self.port))
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
        self.handle_message(msg)

    def handle_message(self, msg):
        # Handle an ACK message
        parts = msg.split(CommandSep)
        if parts[0] == CommandAck:
            id = parts[1]
            self.command_ack_map[id] = True

    def has_received_cmd_ack(self, id):
        return id in self.command_ack_map

    def send_command(self, *args):
        # grab current command id and send message
        id = str(self.command_id)
        msg = CommandSep.join((id,) + args) + '\n'
        self.logger.debug('Sending message: %s', msg.rstrip())
        self.push(msg.encode('utf-8'))

        # increment id for next command
        self.command_id += 1

        # wait for ACK
        while not self.has_received_cmd_ack(id):
            pass

    def send_screenshot_command(self, filename):
        self.send_command(CommandScreenshot, filename)

def get_default_device_client():
    return DeviceClient()
