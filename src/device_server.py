import asynchat
import asyncore
import logging
import socket
import sys
import device_client
from device import get_default_device_manager

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
        self.handle_command(msg)

    def send_ack(self, id):
        ''' Sends ACK of completed command with given id to client '''
        self.logger.debug('Sending ACK for command id %s', id)
        msg = device_client.CommandSep.join([device_client.CommandAck, id]) + '\n'
        self.push(msg.encode())

    def handle_command(self, msg):
        parts = msg.split(device_client.CommandSep)
        id = parts[0]
        command = parts[1]
        data = parts[2:]

        if command == device_client.CommandScreenshot:
            self.handle_screenshot(data[0])
        else:
            self.logger.error('Received unknown command: %s', command)

        self.send_ack(id)

    def handle_screenshot(self, filename):
        self.logger.debug('Handling screenshot command with filename: %s', filename)

        self.device_manager.save_screenshot(filename)

class DeviceServer(asyncore.dispatcher):
    '''
    Manages the creation of DeviceMessageHandlers for every incoming Socket client
    '''
    def __init__(self, device_manager, ip = device_client.DefaultCommunicationIP, port = device_client.DefaultCommunicationPort):
        asyncore.dispatcher.__init__(self)
        self.device_manager = device_manager
        self.logger = logging.getLogger('DeviceServer')

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((ip, port))
        self.address = self.socket.getsockname()
        self.listen(1)

    def start(self):
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
    dm = get_default_device_manager()
    server = DeviceServer(dm)
    return server

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    server = get_default_device_server()
    server.start()

if __name__ == "__main__":
    main()
