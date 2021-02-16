""" We do this in Python rather than node, where the process hub actually lives
so that we can easily access the config file. Process hub will run this
from the command line. """

import sys
from config import NUM_MONITORS, MON_NAMES
from config import VYSOR_RECT
from window import move_window_to_screen, set_window_fullscreen


def setup_process_hub_screen(win_name):
    if NUM_MONITORS == 1:
        w = 1920 / 2
        x, y, h = (1920 - w, 0, 1080)
        move_window_to_screen(win_name, x, y, w, h, MON_NAMES[0])
    elif NUM_MONITORS == 2:
        # share with vysor area
        x = VYSOR_RECT[0] + VYSOR_RECT[2]
        y, w, h = (0, 1920 - x, 1080)
        move_window_to_screen(win_name, x, y, w, h, MON_NAMES[1])
    elif NUM_MONITORS == 3:
        # fullscreen!
        set_window_fullscreen(win_name, MON_NAMES[2])


if __name__ == "__main__":
    setup_process_hub_screen(sys.argv[1])
