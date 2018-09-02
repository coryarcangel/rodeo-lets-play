import collections
import logging
import sys

from util import Rect

# Redis for sharing state between all non-monkeyrunner processes
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Monkeyrunner device client / server communication (no redis installation
# in jython :(
DEVICE_HOST = '127.0.0.1'
DEVICE_PORT = 5005

TFNET_CONFIG = {
    'model': 'cfg/tiny-yolo.cfg',
    'load': 'dfbin/tiny-yolo.weights',
    'gpu': 0.5,
    'threshold': 0.1
}

# Extremely Hard Coded (to the galaxy 8) :) (:
VYSOR_RECT = Rect(0, 0, 776, 466)
VYSOR_CAP_AREA = Rect(62, 95, VYSOR_RECT[-2] - 100, VYSOR_RECT[-1] - 80)
VYSOR_WINDOW_NAME = 'Kim'  # 'Vysor'

# Phone Rects
GALAXY8_RECT = Rect(0, 0, 2220, 1080)
CURRENT_PHONE_RECT = GALAXY8_RECT

# Image Configs
ImageConfig = collections.namedtuple("ImageConfig", [
    "width",
    "height",
    "top_menu_height",
    "top_menu_padding",
    "top_menu_item_width",
    "money_item_left",
    "stars_item_left"
])

IMG_CONFIG_IPHONE7PLUS = ImageConfig(
    width=2208,
    height=1242,
    money_item_left=1170,
    stars_item_left=1568,
    top_menu_height=115,
    top_menu_padding=30,
    top_menu_item_width=240
)

IMG_CONFIG_STUDIOBLU = ImageConfig(
    width=1280,
    height=720,
    money_item_left=680,
    stars_item_left=884,
    top_menu_height=60,
    top_menu_padding=10,
    top_menu_item_width=120
)

IMG_CONFIG_GALAXY8 = ImageConfig(
    width=VYSOR_CAP_AREA[2],
    height=VYSOR_CAP_AREA[3],
    money_item_left=VYSOR_CAP_AREA[2] - 325,
    stars_item_left=VYSOR_CAP_AREA[2] - 220,
    top_menu_height=40,
    top_menu_padding=10,
    top_menu_item_width=65
)

CURRENT_IMG_CONFIG = IMG_CONFIG_GALAXY8


def configure_logging():
    logging.basicConfig(
        stream=sys.stdout,
        format='%(asctime)s.%(msecs)03d:%(levelname)s:%(name)s:%(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')
