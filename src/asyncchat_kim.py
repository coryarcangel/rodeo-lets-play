import asynchat
import logging

from config import DEVICE_HOST, DEVICE_PORT

COMMAND_SEP = '|'

class KimCommand(object):
    ACK = 'ACK'
    SCREENSHOT = 'SCREENSHOT'
    RESET = 'RESET'
    DRAG_X = 'DRAG_X'
    TAP = 'TAP'

class AsyncchatKim(asynchat.async_chat):
    '''
    Wrapper around the native very-raw api that attempts to make communcation
    between device_client and device_server easier
    '''

    def __init__(self, host=DEVICE_HOST, port=DEVICE_PORT, logger_name='async_chat', py2=False, sock=None):
        asynchat.async_chat.__init__(self, sock)
        self.host = host
        self.port = port
        self.logger = logging.getLogger(logger_name)
        self.command_id = 0
        self.command_ack_map = {}
        self.buffer = []
        self.set_terminator('\n')
        self.comm = None
        self.py2 = py2

    def collect_incoming_data(self, data):
        self.buffer.append(data if self.py2 else data.decode())

    def found_terminator(self):
        msg = ''.join(self.buffer)
        self.logger.debug('received message: %s', msg)
        self.buffer = []
        self._handle_message(msg)

    def _handle_message(self, msg):
        parts = msg.split(COMMAND_SEP)
        command_id, command, data = parts[0], parts[1], parts[2:]
        self._handle_command(command_id, command, data)

    def _handle_command(self, command_id, command, data):
        print('need to handle %s' % command)

    def _send_message(self, msg):
        self.logger.debug('Sending message: %s', msg.rstrip())
        self.push(msg.encode() if self.py2 else msg.encode('utf-8'))

    def _send_command(self, *args):
        # grab current command id and send message
        command_id = str(self.command_id)
        msg = COMMAND_SEP.join((command_id,) + args) + '\n'
        self._send_message(msg)

        # increment id for next command
        self.command_id += 1

    def send_ack(self, command_id):
        ''' Sends ACK of completed command with given id '''
        msg = COMMAND_SEP.join((command_id, KimCommand.ACK)) + '\n'
        self._send_message(msg)
