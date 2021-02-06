import collections

from util import Rect

# Redis for sharing state between all non-monkeyrunner processes
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Monkeyrunner device client / server communication (no redis installation
# in jython :(
DEVICE_HOST = '127.0.0.1'
DEVICE_PORT = 5005

FRONTEND_WEB_URL = 'http://localhost:8888'
FRONTEND_NAME = 'KIM_FRONTEND'  # 'hollywood - Google Chrome'

KILL_ADB_ON_DEVICE_SERVER_EXIT = False

# Areas of the device that are not clickable if device_client.safeguard_menu_clicks
# is set to True (useful in training).
SAFEGUARD_MENU_CLICKS_DEFAULT = False
SAFEGUARD_MENU_RECTS = [
    Rect(0, 0, 3000, 100),  # the entire top bar is bad news
    Rect(1350, 940, 550, 200),  # all the buttons in bottom right except checkmark
]

# Galaxy 10
GALAXY10_RECT = Rect(0, 0, 2280, 1080)
GALAXY10_GAME_RECT = Rect(112, 0, 2168, 1080)

HEN_VYSOR_RECT = Rect(10, 10, 1665, 827)
HEN_OPTIONS = {
    'MONITORS': [
        ('HDMI-1-1', (1920, 1080)),
        ('DP-1', (1920, 1080)),
        ('DP-3', (1920, 1080))
    ],
    'TFNET_CONFIG': {
        'model': 'cfg/tiny-yolo.cfg',
        'load': 'dfbin/tiny-yolo.weights',
        'gpu': 0.75,
        'threshold': 0.07
    },
    'TF_DEEPQ_POLICY_SAVE_DIR': 'grid_deep_q_1',
    'TF_AI_POLICY_WEIGHTS': {
        'deep_q': 0.5,
        'heuristic': 0.4,
        'random': 0.1
    },
    'VYSOR_RECT': HEN_VYSOR_RECT,
    'PHONE_RECT': GALAXY10_RECT,
    'PHONE_GAME_RECT': GALAXY10_GAME_RECT,
    'PHONE_VYSOR_CAP_AREA': Rect(92, 71, HEN_VYSOR_RECT[-2] - 83, HEN_VYSOR_RECT[-1] - 37),
    'IMAGE_PROCESS_SCALE': 0.75,
    'HOUGH_CIRCLES_CONFIG': {
        'dp': 0.25,  # (inverse ratio of accumulator resolution)
        'minDist': 30,  # min distance between circles
        'param1': 500,  # (confusing)
        'param2': 50,  # (smaller means more false circles)
        'minRadius': 5,
        'maxRadius': 100
    }
}

# Galaxy 8
GALAXY8_RECT = Rect(0, 0, 2220, 1080)  # Raw Phone Size
GALAXY8_GAME_RECT = Rect(146, 25, 1928, 1060)  # Account for black space

KEV_VYSOR_RECT = Rect(0, 0, 776, 466)
KEV_OPTIONS = {
    'MONITORS': [
        ('HDMI-1-1', (1920, 1080)),
        ('DP-1', (1920, 1080)),
    ],
    'TFNET_CONFIG': {
        'model': 'cfg/tiny-yolo.cfg',
        'load': 'dfbin/tiny-yolo.weights',
        'gpu': 0.5,
        'threshold': 0.1
    },
    'TF_DEEPQ_POLICY_SAVE_DIR': 'grid_deep_q_1',
    'TF_AI_POLICY_WEIGHTS': {
        'deep_q': 0.5,
        'heuristic': 0.4,
        'random': 0.1
    },
    'VYSOR_RECT': KEV_VYSOR_RECT,
    'PHONE_RECT': GALAXY8_RECT,
    'PHONE_GAME_RECT': GALAXY8_GAME_RECT,
    'PHONE_VYSOR_CAP_AREA': Rect(52, 68, KEV_VYSOR_RECT[-2] - 105, KEV_VYSOR_RECT[-1] - 82),
    'IMAGE_PROCESS_SCALE': 1,
    'HOUGH_CIRCLES_CONFIG': {
        'dp': 0.25,  # (inverse ratio of accumulator resolution)
        'minDist': 30,  # min distance between circles
        'param1': 500,  # (confusing)
        'param2': 40,  # (smaller means more false circles)
        'minRadius': 2,
        'maxRadius': 30
    }
}

OPTIONS = KEV_OPTIONS

# monitor config is system dependent
MONITORS = OPTIONS['MONITORS']

NUM_MONITORS = len(MONITORS)
MON_NAMES = [s[0] for s in MONITORS]

SCREEN_SIZES = {}
for s in MONITORS:
    SCREEN_SIZES[s[0]] = s[1]

TFNET_CONFIG = OPTIONS['TFNET_CONFIG']

TF_DEEPQ_POLICY_SAVE_DIR = OPTIONS['TF_DEEPQ_POLICY_SAVE_DIR']

TF_AI_POLICY_WEIGHTS = OPTIONS['TF_AI_POLICY_WEIGHTS']

# Where the Vysor Window Is Moved To
VYSOR_RECT = OPTIONS['VYSOR_RECT']
IMAGE_PROCESS_SCALE = OPTIONS['IMAGE_PROCESS_SCALE']

# Name of the phone in vysor (change in vysor settings)
VYSOR_WINDOW_NAME = 'VysorKim'

HOUGH_CIRCLES_CONFIG = OPTIONS['HOUGH_CIRCLES_CONFIG']

CONTOUR_PROCESS_WIDTH = 300

"""
Phone Rect / Game Rect is about the raw phone size.
These two things are related...

Vysor cap area is area of the screen to capture for phone image stream
(handles game aspect ratio).
"""

CURRENT_PHONE_GAME_RECT = OPTIONS['PHONE_GAME_RECT']
VYSOR_CAP_AREA = OPTIONS['PHONE_VYSOR_CAP_AREA']

# Image Configs
ImageConfig = collections.namedtuple("ImageConfig", [
    "width",
    "height",
    "top_menu_height",
    "top_menu_padding",
    "top_menu_item_width",
    "money_item_left",
    "stars_item_left",
    "bolts_item_left",
])

IMG_CONFIG_IPHONE7PLUS = ImageConfig(
    width=2208,
    height=1242,
    money_item_left=1170,
    stars_item_left=1568,
    bolts_item_left=0,
    top_menu_height=115,
    top_menu_padding=30,
    top_menu_item_width=240
)

IMG_CONFIG_STUDIOBLU = ImageConfig(
    width=1280,
    height=720,
    money_item_left=680,
    stars_item_left=884,
    bolts_item_left=0,
    top_menu_height=60,
    top_menu_padding=10,
    top_menu_item_width=120
)

IMG_CONFIG_GALAXY8 = ImageConfig(
    width=VYSOR_CAP_AREA[2],
    height=VYSOR_CAP_AREA[3],
    money_item_left=VYSOR_CAP_AREA[2] - 312,
    stars_item_left=VYSOR_CAP_AREA[2] - 205,
    bolts_item_left=VYSOR_CAP_AREA[2] - 407,
    top_menu_height=40,
    top_menu_padding=10,
    top_menu_item_width=55
)

IMG_CONFIG_GALAXY10 = ImageConfig(
    width=VYSOR_CAP_AREA[2],
    height=VYSOR_CAP_AREA[3],
    money_item_left=VYSOR_CAP_AREA[2] - 752,
    stars_item_left=VYSOR_CAP_AREA[2] - 542,
    bolts_item_left=VYSOR_CAP_AREA[2] - 407,
    top_menu_height=64,
    top_menu_padding=20,
    top_menu_item_width=120
)

# TODO: IMG_CONFIG_GALAXY10

CURRENT_IMG_CONFIG = IMG_CONFIG_GALAXY10
