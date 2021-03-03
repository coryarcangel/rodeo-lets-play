import asynchat
from random import randint
from kim_logs import get_kim_logger
from config import DEVICE_HOST, DEVICE_PORT

COMMAND_SEP = '|'


class KimCommand(object):
    ACK = 'ACK'
    GET_PROCESS = 'GET_PROCESS'
    SCREENSHOT = 'SCREENSHOT'
    RESET = 'RESET'
    DRAG_X = 'DRAG_X'
    TAP = 'TAP'
    DOUBLE_TAP = 'DOUBLE_TAP'
    BACK_BUTTON = 'BACK_BUTTON'
    LAUNCH_HOLLYWOOD = 'LAUNCH_HOLLYWOOD'


class AsyncchatKim(asynchat.async_chat):
    '''
    Wrapper around the native very-raw api that attempts to make communcation
    between device_client and device_server easier
    '''

    def __init__(self, host=DEVICE_HOST, port=DEVICE_PORT,
                 logger_name='async_chat', py2=False, sock=None):
        asynchat.async_chat.__init__(self, sock)
        self.sock = sock
        self.host = host
        self.port = port
        self.logger = get_kim_logger(logger_name)
        self.command_ack_map = {}
        self.command_res_queue = []
        self.comm = None
        self.py2 = py2
        self.use_encoding = True
        self.set_terminator('\n'.encode())
        self.buffer = []

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
        if command == KimCommand.ACK:
            self._handle_ack(command_id, data)
        else:
            self._handle_command(command_id, command, data)

    def _handle_ack(self, command_id, data):
        # self.logger.debug('Received ACK for %s', command_id)
        self.command_ack_map[command_id] = True
        self.command_res_queue.append((command_id, data))

        # remove old ack / response data to save on memory
        if len(self.command_res_queue) > 10:
            old_id, _ = self.command_res_queue.pop(0)
            if old_id in self.command_ack_map:
                del self.command_ack_map[old_id]

    def _handle_command(self, command_id, command, data):
        self.logger.debug('need to handle %s' % command)

    def _has_received_cmd_ack(self, command_id):
        return command_id in self.command_ack_map

    def _send_message(self, msg):
        self.logger.debug('Sending message: %s', msg.rstrip())
        self.push(msg.encode())

    def _send_command(self, *args):
        # grab current command id and send message
        command_id = str(randint(1, 99999999))
        msg = COMMAND_SEP.join([command_id] + [str(a) for a in args]) + '\n'
        self._send_message(msg)
        return command_id

    def send_ack(self, command_id, res_data):
        ''' Sends ACK of completed command with given id and optional data '''
        parts = [command_id, KimCommand.ACK]
        if res_data is not None:
            parts.append(res_data)

        msg = COMMAND_SEP.join(parts) + '\n'
        self._send_message(msg)

    def get_command_res_data(self, command_id):
        """ finds res_data from given command if it still exists in deque """
        for id, data in self.command_res_queue:
            if id == command_id:
                return data

        return None
