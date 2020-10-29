'''
Very simple process that opens chrome to the frontend server url and sets
the window to the proper place
'''

import time
import sys

from config import FRONTEND_WEB_URL, FRONTEND_NAME
from window import set_window_rect, open_chrome_url, click_in_window, get_window_id
from kim_current_app_monitor import KimCurrentAppMonitor


def log(text):
    print(text, file=sys.stdout)
    sys.stdout.flush()


def run_frontend_client():
    """
    Two jobs:
        1. Open chrome to the frontend view, and ensure chrome doesnt die.
        2. Run the KimCurrentAppMonitor loop.
    """

    chrome_p = None
    try:
        log('Opening Chrome to Frontend at {}'.format(FRONTEND_WEB_URL))
        chrome_p = open_chrome_url(FRONTEND_WEB_URL, bg=True)

        # ** wait for the chrome to open
        time.sleep(2)

        # ** Move Chrome to the correct place
        # set_window_fullscreen(FRONTEND_NAME)
        win_id = get_window_id(FRONTEND_NAME)
        set_window_rect(win_id, 800, 50, 1080, 608)

        # ** remove the "chrome didnt shut down correctly"
        # click_in_window(win_id, 800, 100)

        kim_monitor = KimCurrentAppMonitor()

        while True:
            code = chrome_p.poll()
            if chrome_p and code is not None:
                # chrome has exited, abort!
                log('Restarting due to dead Chrome: exit code {}'.format(code))
                sys.exit()

            kim_monitor.run_monitor_loop()

            time.sleep(1)

    except (KeyboardInterrupt, SystemExit) as e:
        log("Caught closure exception")
        if chrome_p:
            chrome_p.terminate()


if __name__ == '__main__':
    run_frontend_client()
