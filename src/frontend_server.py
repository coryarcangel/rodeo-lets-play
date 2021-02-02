#!/usr/bin/env python3

import argparse
import os
import io
import json
import redis

import tornado.ioloop
import tornado.web
import tornado.websocket

from PIL import Image

from config import REDIS_HOST, REDIS_PORT, VYSOR_CAP_AREA
from kim_logs import get_kim_logger
from ai_actions import ActionGetter
from ai_state_data import AIState

script_path = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Start the PyImageStream server.')

parser.add_argument('--port', default=8888, type=int, help='Web server port (default: 8888)')
parser.add_argument('--width', default=VYSOR_CAP_AREA.w, type=int, help='Width (default to VYSOR_CAP_AREA.width)')
parser.add_argument('--height', default=VYSOR_CAP_AREA.h, type=int, help='Height (default to VYSOR_CAP_AREA.height)')
parser.add_argument('--quality', default=90, type=int, help='JPEG Quality 1 (worst) to 100 (best) (default: 90)')
parser.add_argument('--stopdelay', default=7, type=int, help='Delay in seconds before the camera will be stopped after '
                                                             'all clients have disconnected (default: 7)')
args = parser.parse_args()


logger = get_kim_logger('FrontendServer')


def log(text):
    logger.info(text)


class FrontendRedisStream:
    def __init__(self, width, height, quality):
        log("Initializing FrontendRedisStream...")

        self.phone_image_state_data = None
        self.phone_image_state_obj = None
        self.phone_image_index = 0
        self.on_ai_log_line = None
        self.on_ai_action = None
        self.system_info_data = {}
        self.ai_status_data = {}
        self.size = (width, height)
        self.quality = quality

        self.r = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=False)

        self.pubsub = self.r.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{
            'phone-image-states': self._handle_phone_image_state,
            'system-info-updates': self._handle_system_info_update,
            'ai-status-updates': self._handle_ai_status_updates,
            'ai-log-lines': self._handle_ai_log_line,
            'ai-action-stream': self._handle_ai_action_stream,
        })
        self.pubsub.run_in_thread(sleep_time=0.001)

    def _get_message_data(self, message, isjson=True):
        if message['type'] != 'message':
            return None

        text = message['data'].decode('utf-8')
        return json.loads(text) if isjson else text

    def _handle_phone_image_state(self, message):
        data = self._get_message_data(message)
        if data:
            self.phone_image_state_data = data['state']
            self.phone_image_state_obj = AIState.deserialize(self.phone_image_state_data)
            self.phone_image_index = data['index']

    def _handle_system_info_update(self, message):
        data = self._get_message_data(message)
        if data:
            self.system_info_data = data

    def _handle_ai_status_updates(self, message):
        data = self._get_message_data(message)
        if data:
            self.ai_status_data = data

    def _handle_ai_log_line(self, message):
        line = self._get_message_data(message, isjson=False)
        if line and self.on_ai_log_line:
            self.on_ai_log_line(line)

    def _handle_ai_action_stream(self, message):
        data = self._get_message_data(message)
        if data and self.on_ai_action:
            self.on_ai_action(data)

    def get_jpeg_image_bytes(self):
        image_data = self.r.get('phone-image-data')
        if not image_data or not self.phone_image_state_obj:
            return None

        shape = self.phone_image_state_obj.image_shape
        decoded = Image.frombytes('RGB', (shape[0], shape[1]), image_data)
        pimg = decoded.resize(self.size, Image.ANTIALIAS)

        with io.BytesIO() as bytesIO:
            pimg.save(bytesIO, "JPEG", quality=self.quality, optimize=True)
            return bytesIO.getvalue()


redis_stream = FrontendRedisStream(args.width, args.height, args.quality)


class ServerWebSocketHandler(tornado.websocket.WebSocketHandler):
    clients = set()

    def __init__(self, *args, **kwargs):
        super(ServerWebSocketHandler, self).__init__(*args, **kwargs)
        redis_stream.on_ai_log_line = self.queue_ai_log_line
        redis_stream.on_ai_action = self.queue_ai_action
        self.message_queue = []

    def check_origin(self, origin):
        # Allow access from every origin
        return True

    def open(self):
        ServerWebSocketHandler.clients.add(self)
        log("WebSocket opened from: " + self.request.remote_ip)

    def queue_message(self, message):
        self.message_queue.append(message)

    def queue_ai_log_line(self, line):
        self.queue_message({'type': 'aiLogLine', 'data': line})

    def queue_ai_action(self, data):
        self.queue_message({'type': 'aiAction', 'data': data})

    def write_cur_state(self):
        data = {
            'frameNum': redis_stream.phone_image_index,
            'imageState': redis_stream.phone_image_state_data,
            'systemInfo': redis_stream.system_info_data,
            'aiStatus': redis_stream.ai_status_data,
        }
        self.write_message({'type': 'curState', 'data': data})

    def on_message(self, message):
        jpeg_bytes = redis_stream.get_jpeg_image_bytes()
        if jpeg_bytes:
            self.write_message(jpeg_bytes, binary=True)

        self.write_cur_state()

        for q_message in self.message_queue:
            self.write_message(q_message)
        self.message_queue = []

    def on_close(self):
        ServerWebSocketHandler.clients.remove(self)
        log("WebSocket closed from: " + self.request.remote_ip)


static_path = script_path + '/../frontend-static/'

server_url = "http://localhost:" + str(args.port)
log("Starting server: " + server_url)

app = tornado.web.Application([
        (r"/websocket", ServerWebSocketHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {'path': static_path, 'default_filename': 'index.html'}),
    ])
app.listen(args.port)

tornado.ioloop.IOLoop.current().start()
