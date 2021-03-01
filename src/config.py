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
DASHBOARD_NAME = 'AI_DASHBOARD'

# Name of the phone in vysor (change in vysor settings)
VYSOR_WINDOW_NAME = 'VysorKim'

# Android app stuff
KK_HOLLYWOOD_PACKAGE = 'com.glu.stardomkim'
KK_HOLLYWOOD_COMPONENT = '%s/com.google.android.vending.expansion.downloader_impl.DownloaderActivity' % KK_HOLLYWOOD_PACKAGE

RESET_PACKAGES_TO_KILL = [
    'com.facebook.katana',
    'com.google.android.gms',
    'com.google.android.play.games',
]

"""
SYSTEM SPECIFIC CONFIG (PHONE, COMP, ETC)
"""

# Galaxy 10
GALAXY10_RECT = Rect(0, 0, 2280, 1080)
GALAXY10_GAME_RECT = Rect(112, 0, 2168, 1080)

HEN_VYSOR_RECT = Rect(10, 10, 1665, 827)
HEN_OPTIONS = {
    'MONITORS': [
        ('HDMI-0', (1920, 1080)),
        ('DP-1', (1920, 1080)),
        ('DP-3', (1920, 1080))
    ],
    'TFNET_CONFIG': {
        'model': 'cfg/tiny-yolo.cfg',
        'load': 'dfbin/tiny-yolo.weights',
        'gpu': 0.75,
        'threshold': 0.075
    },
    'TF_DEEPQ_POLICY_SAVE_DIR': 'new_tap_swipe_rewards',
    'TF_DEEPQ_POLICY_NAME': 'policy_2021_02_27_18_21_05_600',
    'TF_AI_POLICY_WEIGHTS': {
        'deep_q': 0.4,
        'heuristic': 0.5,
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
        'param2': 55,  # (smaller means more false circles)
        'minRadius': 22,
        'maxRadius': 75
    },
    'CENTER_Y_OFFSET': 105,
    'SAFEGUARD_MENU_RECTS': [
        Rect(0, 0, 3000, 120),  # the entire top bar is bad news
        Rect(1600, 940, 550, 200),  # all the buttons in bottom right except checkmark
        Rect(1895, 0, 1000, 345),  # the special E / fans / etc thing in the top right
    ],
    'ACTION_SHAPE_COLOR_RANGES': [
        ShapeColorRange(ActionShape.MENU_EXIT, 'Red',
                        lower=(-2, 125, 200), upper=(1, 255, 255),
                        min_area=200, max_area=600, min_verts=4, max_verts=9, max_area_ratio=2),
        ShapeColorRange(ActionShape.ROOM_EXIT, 'Red',
                        lower=(-4, 25, 180), upper=(4, 255, 255),
                        min_area=1200, max_area=4500, min_verts=9, max_verts=30, max_area_ratio=2),
        ShapeColorRange(ActionShape.AREA_ENTRY, 'Gold',  # gold perimeters
                        lower=(20, 25, 180), upper=(30, 255, 255),
                        min_area=800, max_area=4500, min_verts=8, max_verts=30, min_area_ratio=1.4, max_area_ratio=6),
        ShapeColorRange(ActionShape.STRONG_TALK_CHOICE, 'Light Blue',  # most common action
                        lower=(100, 200, 50), upper=(120, 255, 255),
                        min_area=600, max_area=9000, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Azure',
                        lower=(104, 50, 200), upper=(107, 90, 255),
                        min_area=3500, max_area=7500, min_verts=4, max_verts=15, max_area_ratio=1.25),  # deal with azure backgrounds
        ShapeColorRange(ActionShape.MONEY_CHOICE, 'Light Green',  # money green
                        lower=(40, 100, 50), upper=(65, 255, 255),
                        min_area=800, max_area=9000, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Light Gray',  # usually cancel
                        lower=(0, 15, 170), upper=(255, 25, 195),
                        min_area=2500, max_area=8500, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Pink',  # flirting
                        lower=(160, 120, 120), upper=(170, 255, 255),
                        min_area=600, max_area=9000, min_verts=4, max_verts=15, max_area_ratio=2.3),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Teal',
                        lower=(93, 175, 50), upper=(96, 255, 200),
                        min_area=320, max_area=9000, min_verts=4, max_verts=25, max_area_ratio=1.9),
        ShapeColorRange(ActionShape.IMPORTANT_MARKER, 'Yellow',  # yellow exclamation marks
                        lower=(23, 100, 50), upper=(30, 255, 255),
                        min_area=300, max_area=2500, min_verts=4, max_verts=30),
        ShapeColorRange(ActionShape.MAYBE_TALK_CHOICE, 'White',  # circular white "..."
                        lower=(0, 0, 225), upper=(255, 5, 255),
                        min_area=1050, max_area=1500, min_verts=11, max_verts=20, max_area_ratio=2),
        ShapeColorRange(ActionShape.MAYBE_TALK_CHOICE, 'White',  # huge white boxes
                        lower=(0, 0, 240), upper=(255, 10, 255),
                        min_area=12000, max_area=50000, min_verts=4, max_verts=25, max_area_ratio=1.65),
        ShapeColorRange(ActionShape.CONFIRM_OK, 'White',  # white rects with gold / silver perimeter
                        lower=(0, 0, 245), upper=(255, 2, 255),
                        min_area=900, max_area=3500, min_verts=5, max_verts=18, max_area_ratio=1.45),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Orange',
                        lower=(14, 200, 200), upper=(15, 255, 255),
                        min_area=800, max_area=9000, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Violet',
                        lower=(152, 175, 150), upper=(154, 255, 200),
                        min_area=320, max_area=9000, min_verts=4, max_verts=25, max_area_ratio=1.9),
        ShapeColorRange(ActionShape.COLLECTABLE, 'Green',  # clickable money
                        lower=(40, 100, 50), upper=(52, 255, 255),
                        min_area=100, max_area=500, min_verts=8, max_verts=20,
                        min_y=240, min_area_ratio=1.2, max_area_ratio=2),
        ShapeColorRange(ActionShape.COLLECTABLE, 'Aqua',  # clickable stars :)
                        lower=(87, 50, 50), upper=(95, 255, 255),
                        min_area=260, max_area=800, min_verts=13, max_verts=25,
                        min_y=240, min_area_ratio=1.5, max_area_ratio=3),
        ShapeColorRange(ActionShape.COLLECTABLE, 'Khaki',  # clickable people :)
                        lower=(17, 50, 120), upper=(24, 150, 255),
                        min_area=610, max_area=1100, min_verts=8, max_verts=30,
                        min_y=240, min_area_ratio=1.2, max_area_ratio=3),
    ]
}

# Galaxy 8
GALAXY8_RECT = Rect(0, 0, 2220, 1080)  # Raw Phone Size
GALAXY8_GAME_RECT = Rect(146, 25, 1928, 1060)  # Account for black space

KEV_VYSOR_RECT = Rect(0, 0, 776, 466)
KEV_OPTIONS = {
    'MONITORS': [
        ('HDMI-1-1', (1920, 1080)),
        # ('DP-1', (1920, 1080)),
    ],
    'TFNET_CONFIG': {
        'model': 'cfg/tiny-yolo.cfg',
        'load': 'dfbin/tiny-yolo.weights',
        'gpu': 0.5,
        'threshold': 0.05
    },
    'TF_DEEPQ_POLICY_SAVE_DIR': 'new2_qnn_and_rewards',
    'TF_DEEPQ_POLICY_NAME': 'policy',
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
    },
    'CENTER_Y_OFFSET': 35,
    'SAFEGUARD_MENU_RECTS': [
        Rect(0, 0, 3000, 100),  # the entire top bar is bad news
        Rect(1350, 940, 550, 200),  # all the buttons in bottom right except checkmark
        Rect(1895, 0, 1000, 345),  # the special E / fans / etc thing in the top right
    ],
    'ACTION_SHAPE_COLOR_RANGES': [
        ShapeColorRange(ActionShape.MENU_EXIT, 'Red',
                        lower=(-2, 125, 200), upper=(1, 255, 255),
                        min_area=200, max_area=600, min_verts=4, max_verts=9, max_area_ratio=2),
        ShapeColorRange(ActionShape.ROOM_EXIT, 'Red',
                        lower=(-2, 25, 200), upper=(1, 255, 255),
                        min_area=1200, max_area=4500, min_verts=11, max_verts=30),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Light Blue',  # most common action
                        lower=(100, 160, 50), upper=(120, 255, 255),
                        min_area=600, max_area=9000, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Azure',
                        lower=(102, 50, 200), upper=(105, 100, 255),
                        min_area=3500, max_area=7500, min_verts=4, max_verts=15, max_area_ratio=1.2),  # deal with azure backgrounds
        ShapeColorRange(ActionShape.MONEY_CHOICE, 'Light Green',  # money green
                        lower=(40, 100, 50), upper=(65, 255, 255),
                        min_area=800, max_area=9000, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Light Gray',  # usually cancel
                        lower=(0, 15, 170), upper=(255, 25, 195),
                        min_area=2500, max_area=8500, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Pink',  # flirting
                        lower=(160, 20, 20), upper=(170, 255, 255),
                        min_area=600, max_area=9000, min_verts=4, max_verts=15, max_area_ratio=2.3),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Teal',
                        lower=(90, 150, 50), upper=(95, 255, 200),
                        min_area=320, max_area=9000, min_verts=4, max_verts=15, max_area_ratio=1.7),
        ShapeColorRange(ActionShape.IMPORTANT_MARKER, 'Yellow',  # yellow exclamation marks
                        lower=(23, 100, 50), upper=(30, 255, 255),
                        min_area=300, max_area=2500, min_verts=4, max_verts=30),
        ShapeColorRange(ActionShape.MAYBE_TALK_CHOICE, 'White',  # circular white "..."
                        lower=(0, 0, 225), upper=(255, 5, 255),
                        min_area=1050, max_area=1500, min_verts=11, max_verts=20, max_area_ratio=2),
        ShapeColorRange(ActionShape.MAYBE_TALK_CHOICE, 'White',  # huge white boxes
                        lower=(0, 0, 235), upper=(255, 5, 255),
                        min_area=12000, max_area=50000, min_verts=4, max_verts=25, max_area_ratio=1.2),
        ShapeColorRange(ActionShape.CONFIRM_OK, 'White',  # white rects with gold / silver perimeter
                        lower=(0, 0, 245), upper=(255, 2, 255),
                        min_area=900, max_area=10000, min_verts=5, max_verts=18, max_area_ratio=1.25),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Orange',
                        lower=(14, 50, 200), upper=(15, 255, 255),
                        min_area=800, max_area=9000, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.TALK_CHOICE, 'Violet',  # TODO: need to Violet see in practice
                        lower=(153, 180, 150), upper=(157, 205, 215),
                        min_area=320, max_area=9000, min_verts=4, max_verts=15),
        ShapeColorRange(ActionShape.COLLECTABLE, 'Green',  # clickable money
                        lower=(40, 100, 50), upper=(52, 255, 255),
                        min_area=100, max_area=500, min_verts=8, max_verts=20,
                        min_y=275, min_area_ratio=1.2, max_area_ratio=2),
        ShapeColorRange(ActionShape.COLLECTABLE, 'Aqua',  # clickable stars :)
                        lower=(87, 50, 50), upper=(95, 255, 255),
                        min_area=380, max_area=800, min_verts=13, max_verts=25,
                        min_y=275, min_area_ratio=1.5, max_area_ratio=3),
        ShapeColorRange(ActionShape.COLLECTABLE, 'Khaki',  # clickable people :)
                        lower=(17, 50, 120), upper=(24, 150, 255),
                        min_area=700, max_area=1100, min_verts=8, max_verts=30,
                        min_y=275, min_area_ratio=1.2, max_area_ratio=3),

        # ShapeColorRange(ActionShape.COLLECTABLE, 'PowderBlue',  # clickable lightning :)
        #                 lower=(70, 15, 150), upper=(100, 80, 255),
        #                 min_area=500, max_area=1100, min_verts=8, max_verts=30, min_area_ratio=1.5, max_area_ratio=2),
        # ShapeColorRange(ActionShape.CONFIRM_OK, 'Gold',  # gold perimeters
        #                 lower=(10, 75, 100), upper=(20, 255, 255),
        #                 min_area=800, max_area=9000, min_verts=8, max_verts=20, min_area_ratio=3, max_area_ratio=8),
    ]
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
TF_DEEPQ_POLICY_NAME = OPTIONS['TF_DEEPQ_POLICY_NAME']

TF_AI_POLICY_WEIGHTS = OPTIONS['TF_AI_POLICY_WEIGHTS']

# Where the Vysor Window Is Moved To
VYSOR_RECT = OPTIONS['VYSOR_RECT']
IMAGE_PROCESS_SCALE = OPTIONS['IMAGE_PROCESS_SCALE']

HOUGH_CIRCLES_CONFIG = OPTIONS['HOUGH_CIRCLES_CONFIG']
SAFEGUARD_MENU_RECTS = OPTIONS['SAFEGUARD_MENU_RECTS']
CENTER_Y_OFFSET = OPTIONS['CENTER_Y_OFFSET']

"""
REWARD CALCULATION
"""

REWARD_PARAMS = {
    'money_mult': 50,
    'stars_mult': 100,
    'money_memory': 25,
    'stars_memory': 25,
    'action_memory': 25,
    'max_repeat_swipes_in_memory': 2,
    'max_repeat_object_taps_in_memory': 2,
    'repeat_tap_distance_threshold': 24,
    'swipe_reward': 1.2,
    'object_type_tap_rewards': [('action_shape', 4), ('circle', 1)],
    'color_sig_change_reward': 2,
    'repeat_tap_penalty': -4.5,
    'repeat_swipe_penalty': -4,
    'do_nothing_penalty': -0.5,
    'reset_penalty': 10,
}

"""
TRAINING PARAMS
"""

TRAINING_PARAMS = {
    'save_dir': 'new4_obs2_tfa3_qnn',
    'num_iterations': 1000,
    'collect_steps_per_iteration': 100,
    'checkpoint_save_interval': 20,
    'policy_save_interval': 20,
    'max_checkpoints': 4,
    'learning_rate': 0.02,
    'epsilon_greedy': 0.25,
    'fc_layer_params': (200, 40),
    'conv_layer_params': None,
    'gamma': 0.9,
    'replay_buffer_capacity': 100000,
    'train_log_interval': 1,
    'replay_batch_size': 64,
    'train_eval_interval': 100,
    'num_eval_steps': 50,
    'adam_epsilon': 1e-5,
    'assumed_start_steps': 0
}

"""
BEHAVIOR
"""

# NOTE: areas configured to CONTOUR_PROCESS_HEIGHT at 400. Should eventually make this ratio based..
ACTION_SHAPE_COLOR_RANGES = OPTIONS['ACTION_SHAPE_COLOR_RANGES']

DELAY_BETWEEN_ACTIONS = 2  # in seconds

SHELL_TAP_PROB = 0.7  # 0 -> 1, prob will choose between two tap types in device_manager

KILL_ADB_ON_DEVICE_SERVER_EXIT = False

MAX_NO_MONEY_READ_TIME = 30  # seconds
MAX_NO_MONEY_READ_BACK_BUTTON_ATTEMPTS = 5
MAX_NON_KIM_APP_TIME = 10  # seconds we can not be in the KK:H app. Fallback from no money fixes.

SECONDS_BETWEEN_BACK_BUTTONS = 1.3

CONTOUR_PROCESS_HEIGHT = 400  # height of images processed in image_contours

COLOR_SIG_K = 3
COLOR_SIG_PCT_FACTOR = 0.05
COLOR_SIG_SQUASH_FACTOR = 0.03

# Areas of the device that are not clickable if set to True (useful in training).
SAFEGUARD_MENU_CLICKS_DEFAULT = True

ACTION_WEIGHTS = {
    Action.PASS: 50,
    Action.SWIPE_LEFT: 3000,  # push forward more than back
    Action.SWIPE_RIGHT: 2500,
    Action.TAP_LOCATION: 100,
    Action.DOUBLE_TAP_LOCATION: 10,
    Action.RESET: 40,
}

TAP_TYPE_ACTION_WEIGHTS = {
    'menu': 1,
    'hot_region': 500,
    'object': 50
}

TAP_OBJECT_ACTION_WEIGHTS = {
    'frisbee': 300,
    'circle': 300,
    'clock': 150,
    'sports ball': 150,
    'traffic light': 10,
    'doorbell': 250,
    'person': 5,
    'umbrella': 5,
    'chair': 5
}

DARKNET_SPECIFIC_OBJECT_THRESHOLDS = {
    'person': 0.2,
    'bicycle': 0.07,
    'clock': 0.12,
    'traffic light': 0.15
}

# see heuristic_selector.py for documentation
HEURISTIC_CONFIG = {
    'REPEAT_ACTION_DEPRESS': True,
    'RECENT_ROOM_MEMORY': True,
    'COLOR_ACTION_DETECT': True,

    'max_room_history_len': 50,
    'action_shape_tap_max_depression': 0.2,
    'object_tap_max_depression': 0.38,
    'other_action_max_depression': 0.02,
    'num_repeats_to_max_action_depression': 6,
    'action_sel_depress_exp': 1.0,
    'image_sig_stag_limit': 60,
    'large_blob_threshold': 200,
    'large_blob_weight_mult': 2,
    'recent_room_threshold': 3,
    'same_room_threshold': 500,
    'recent_room_exit_weight': 2000,
    'same_room_exit_weight': 2500,
    'no_money_exit_weight': 800,
    'default_exit_weight': 400,

    'blob_dom_color_weights': {
        'red': 300, 'green': 600, 'blue': 1000, 'black': 200, 'white': 1000, 'other': 80
    },

    'action_shape_tap_weights': {
        ActionShape.MENU_EXIT: 100000,
        ActionShape.CONFIRM_OK: 10000,
        ActionShape.AREA_ENTRY: 500,
        ActionShape.MONEY_CHOICE: 3000,
        ActionShape.STRONG_TALK_CHOICE: 6000,
        ActionShape.TALK_CHOICE: 4000,
        ActionShape.COLLECTABLE: 4000,
        ActionShape.MAYBE_TALK_CHOICE: 3000,
        ActionShape.IMPORTANT_MARKER: 2000,
        ActionShape.ROOM_EXIT: 500,
        ActionShape.UNKNOWN: 100
    }
}


def GET_OBJECT_TAP_POINT_NOISE(obj):
    a_shape = obj['shape_data']['action_shape'] if 'shape_data' in obj else None
    color = obj['shape_data']['color_label'] if 'shape_data' in obj else None
    area = obj['shape_data']['boundsArea'] if 'shape_data' in obj else None

    # allow yellow exclamation marks to be tapped around kind of randomly
    if a_shape == ActionShape.IMPORTANT_MARKER and color == 'Yellow':
        return 5.0

    # "..." boxes should be clicked right in the center I guess
    if a_shape == ActionShape.MAYBE_TALK_CHOICE and area <= 2000:
        return 0.05

    # default to a 15% reasonable level of noise for variation around imperfect objects
    return 0.15


def GET_KNOWN_TAP_LOCATIONS(img_rect, img_rect_center):
    _, _, w, h = img_rect
    cx, cy = img_rect_center

    bottom_menu_regions = [
        {'type': 'menu', 'x': w - 80 - 51 * i, 'y': h - 28} for i in range(4)]

    qw = int(w * 0.25)
    qh = int(h * 0.25)
    hot_regions = [
        # For pressing the "OK"
        {'type': 'hot_region', 'x': cx, 'y': cy + CENTER_Y_OFFSET},

        # quadrant regions to catch occassional big tappable boxes
        {'type': 'hot_region', 'x': cx + qw, 'y': cy + qh},
        {'type': 'hot_region', 'x': cx + qw, 'y': cy - qh},
        {'type': 'hot_region', 'x': cx - qw, 'y': cy + qh},
        {'type': 'hot_region', 'x': cx - qw, 'y': cy - qh},
    ]

    return bottom_menu_regions + hot_regions


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
    money_item_left=VYSOR_CAP_AREA[2] - 308,
    stars_item_left=VYSOR_CAP_AREA[2] - 201,
    bolts_item_left=VYSOR_CAP_AREA[2] - 403,
    top_menu_height=38,
    top_menu_padding=12,
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
