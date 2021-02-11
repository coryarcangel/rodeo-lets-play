import collections

from util import Rect
from enums import Action, ActionShape, ShapeColorRange

"""
PORTS AND STUFF
"""

# Redis for sharing state between all non-monkeyrunner processes
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Monkeyrunner device client / server communication (no redis installation
# in jython :(
DEVICE_HOST = '127.0.0.1'
DEVICE_PORT = 5005

FRONTEND_WEB_URL = 'http://localhost:8888'
FRONTEND_NAME = 'KIM_FRONTEND'  # 'hollywood - Google Chrome'

# Name of the phone in vysor (change in vysor settings)
VYSOR_WINDOW_NAME = 'VysorKim'

"""
SAFEGUARDING
"""

KILL_ADB_ON_DEVICE_SERVER_EXIT = False

# Areas of the device that are not clickable if device_client.safeguard_menu_clicks
# is set to True (useful in training).
SAFEGUARD_MENU_CLICKS_DEFAULT = True
SAFEGUARD_MENU_RECTS = [
    Rect(0, 0, 3000, 100),  # the entire top bar is bad news
    Rect(1350, 940, 550, 200),  # all the buttons in bottom right except checkmark
]

"""
BEHAVIOR
"""

ACTION_WEIGHTS = {
    Action.PASS: 50,
    Action.SWIPE_LEFT: 1200,
    Action.SWIPE_RIGHT: 1200,
    Action.TAP_LOCATION: 100,
    Action.DOUBLE_TAP_LOCATION: 10,
    Action.RESET: 0.01
}

TAP_TYPE_ACTION_WEIGHTS = {
    'menu': 1,
    'object': 100
}

TAP_OBJECT_ACTION_WEIGHTS = {
    'frisbee': 500,
    'circle': 500,
    'clock': 500,
    'sports ball': 500,
    'traffic light': 10,
    'doorbell': 250,
    'person': 5,
    'umbrella': 5,
    'chair': 5
}

# see heuristic_selector.py for documentation
HEURISTIC_CONFIG = {
    'REPEAT_ACTION_DEPRESS': True,
    'RECENT_ROOM_MEMORY': True,
    'COLOR_ACTION_DETECT': True,

    'max_room_history_len': 100,
    'object_tap_action_max_sel_count': 7,
    'other_action_max_sel_count': 2,
    'object_tap_action_sel_denom': 10,
    'other_action_sel_denom': 100,
    'action_sel_depress_exp': 1.0,
    'image_sig_stag_limit': 500,
    'large_blob_threshold': 200,
    'large_blob_weight_mult': 2,
    'recent_room_threshold': 1,
    'same_room_threshold': 1500,
    'recent_room_exit_weight': 2500,
    'same_room_exit_weight': 2500,
    'no_money_exit_weight': 100,
    'default_exit_weight': 400,

    'blob_dom_color_weights': {
        'red': 300, 'green': 600, 'blue': 1000, 'black': 200, 'white': 1000, 'other': 80
    },

    'action_shape_tap_weights': {
        ActionShape.MENU_EXIT: 10000,
        ActionShape.CONFIRM_OK: 1000,
        ActionShape.MONEY_CHOICE: 2500,
        ActionShape.TALK_CHOICE: 4000,
        ActionShape.MAYBE_TALK_CHOICE: 1000,
        ActionShape.ROOM_EXIT: 100,
        ActionShape.UNKNOWN: 100
    }
}

# label, lower, upper, min_area, max_area, min_verts, max_verts
ACTION_SHAPE_COLOR_RANGES = [
    ShapeColorRange('Light Blue', (100, 160, 50), (120, 255, 255), 200, 2500, 4, 15),
    ShapeColorRange('Light Green', (40, 100, 50), (65, 255, 255), 100, 1600, 4, 12),
    ShapeColorRange('Pink', (160, 20, 20), (170, 255, 255), 100, 1400, 4, 12),
    ShapeColorRange('Orange', (14, 50, 200), (15, 255, 255), 200, 1400, 4, 12),
    ShapeColorRange('Light Gray', (100, 50, 200), (105, 100, 255), 400, 1400, 4, 12),
    ShapeColorRange('Light Gray', (0, 15, 170), (255, 25, 195), 400, 1400, 4, 12),
    ShapeColorRange('Red', (0, 100, 200), (1, 255, 255), 40, 600, 4, 12),
    ShapeColorRange('Red', (0, 25, 150), (1, 255, 255), 120, 200, 11, 30),
    ShapeColorRange('Yellow', (23, 100, 50), (30, 255, 255), 80, 1000, 4, 30),
    ShapeColorRange('Teal', (90, 150, 50), (95, 255, 200), 40, 1600, 4, 25),
    ShapeColorRange('Violet', (153, 180, 150), (157, 205, 215), 40, 1600, 4, 25),  # TODO: need to Violet see in practice
    ShapeColorRange('White', (0, 0, 128), (255, 5, 255), 110, 400, 10, 30),
    ## ShapeColorRange('White', (0, 0, 128), (255, 5, 255), 80, 400, 4, 30),
]

CONTOUR_PROCESS_WIDTH = 300

MAX_NON_KIM_APP_TIME = 8  # seconds we can not be in the KK:H app

"""
REWARD CALCULATION
"""

REWARD_PARAMS = {
    'money_mult': 1.0,
    'stars_mult': 1.0,
    'recent_swipe_threshold': 20,
    'recent_swipe_reward': 150,
}

"""
SYSTEM SPECIFIC CONFIG (PHONE, COMP, ETC)
"""

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
        'param2': 40,  # (smaller means more false circles)
        'minRadius': 3,
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

OPTIONS = HEN_OPTIONS

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

HOUGH_CIRCLES_CONFIG = OPTIONS['HOUGH_CIRCLES_CONFIG']

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

CURRENT_IMG_CONFIG = IMG_CONFIG_GALAXY10
