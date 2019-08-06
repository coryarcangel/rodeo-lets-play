#!/usr/bin/env python3

import argparse
import os
import io

from random import randint

import tornado.ioloop
import tornado.web
import tornado.websocket

from PIL import Image

script_path = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Start the PyImageStream server.')

parser.add_argument('--port', default=8888, type=int, help='Web server port (default: 8888)')
parser.add_argument('--imgpath', default=script_path + '/../src/img/', type=str, help='Path to image to test with')
parser.add_argument('--img1', default='ios_screenshot_1.png', type=str, help='img1 name')
parser.add_argument('--img2', default='speech_actions_ss_01.png', type=str, help='img2 name')
parser.add_argument('--img3', default='speech_actions_ss_02.png', type=str, help='img3 name')
parser.add_argument('--width', default=640, type=int, help='Width (default: 640)')
parser.add_argument('--height', default=480, type=int, help='Height (default: 480)')
parser.add_argument('--quality', default=70, type=int, help='JPEG Quality 1 (worst) to 100 (best) (default: 70)')
parser.add_argument('--stopdelay', default=7, type=int, help='Delay in seconds before the camera will be stopped after '
                                                             'all clients have disconnected (default: 7)')
args = parser.parse_args()

class StaticImageStream:

    def __init__(self, img_srcs, width, height, quality):
        print("Initializing ImageStream...")
        images = [Image.open(src) for src in img_srcs]
        self.images = [img.resize((width, height), Image.ANTIALIAS) for img in images]
        self.image_bytes = [img.tobytes() for img in self.images]
        self.quality = quality

    def get_jpeg_image_bytes(self):
        index = randint(0, len(self.images) - 1)
        pimg = Image.frombytes('RGB', self.images[index].size, self.image_bytes[index])
        with io.BytesIO() as bytesIO:
            pimg.save(bytesIO, "JPEG", quality=self.quality, optimize=True)
            return bytesIO.getvalue()


srcs = [args.imgpath + src for src in [args.img1, args.img2, args.img3]]
image_stream = StaticImageStream(srcs, args.width, args.height, args.quality)


class ImageWebSocket(tornado.websocket.WebSocketHandler):
    clients = set()

    def check_origin(self, origin):
        # Allow access from every origin
        return True

    def open(self):
        ImageWebSocket.clients.add(self)
        print("WebSocket opened from: " + self.request.remote_ip)

        self.frame_num = 0

    def on_message(self, message):
        jpeg_bytes = image_stream.get_jpeg_image_bytes()
        self.write_message(jpeg_bytes, binary=True)
        self.write_message({
            'frameNum': self.frame_num
        })
        self.frame_num += 1

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
