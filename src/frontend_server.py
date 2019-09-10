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

from config import REDIS_HOST, REDIS_PORT

script_path = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Start the PyImageStream server.')

parser.add_argument('--port', default=8888, type=int, help='Web server port (default: 8888)')
parser.add_argument('--width', default=640, type=int, help='Width (default: 640)')
parser.add_argument('--height', default=480, type=int, help='Height (default: 480)')
parser.add_argument('--quality', default=70, type=int, help='JPEG Quality 1 (worst) to 100 (best) (default: 70)')
parser.add_argument('--stopdelay', default=7, type=int, help='Delay in seconds before the camera will be stopped after '
                                                             'all clients have disconnected (default: 7)')
args = parser.parse_args()


class RedisImageStream:

    def __init__(self, width, height, quality):
        print("Initializing RedisImageStream...")

        self.phone_image_state = None
        self.phone_image_index = 0
        self.size = (width, height)
        self.quality = quality

        self.r = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True)

        self.pubsub = self.r.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{
            'phone-image-states': self._handle_phone_image_state
        })
        self.pubsub.run_in_thread(sleep_time=0.001)

    def _handle_phone_image_state(self, message):
        if message['type'] != 'message':
            return

        data = json.loads(message['data'])
        if data:
            self.phone_image_state = data['state']
            self.phone_image_index = data['index']

    def get_jpeg_image_bytes(self):
        image_data = self.r.get('phone-image-data')
        if not image_data:
            return None

        pimg = Image.frombytes('RGB', image_data).resize(self.size, Image.ANTIALIAS)
        with io.BytesIO() as bytesIO:
            pimg.save(bytesIO, "JPEG", quality=self.quality, optimize=True)
            return bytesIO.getvalue()

    def get_jpeg_image_with_state(self):
        data = self.get_jpeg_image_bytes()
        return (self.phone_image_index, self.phone_image_state, data)


image_stream = RedisImageStream(args.width, args.height, args.quality)


class ImageWebSocket(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):
        # Allow access from every origin
        return True

    def open(self):
        ImageWebSocket.clients.add(self)
        print("WebSocket opened from: " + self.request.remote_ip)

    def on_message(self, message):
        frame_num, image_state, jpeg_bytes = image_stream.get_jpeg_image_with_state()
        if jpeg_bytes:
            self.write_message(jpeg_bytes, binary=True)
        self.write_message({
            'frameNum': self.frame_num,
            'imageState': image_state
        })

    def on_close(self):
        ImageWebSocket.clients.remove(self)
        print("WebSocket closed from: " + self.request.remote_ip)


static_path = script_path + '/static/'

app = tornado.web.Application([
        (r"/websocket", ImageWebSocket),
        (r"/(.*)", tornado.web.StaticFileHandler, {'path': static_path, 'default_filename': 'index.html'}),
    ])
app.listen(args.port)

print("Starting server: http://localhost:" + str(args.port) + "/")

tornado.ioloop.IOLoop.current().start()
