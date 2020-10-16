'''
Very simple process that opens chrome to the frontend server url and sets
the window to the proper place
'''

import time
import sys

from config import FRONTEND_WEB_URL, FRONTEND_NAME
from window import set_window_rect, open_chrome_url, click_in_window, get_window_id


def log(text):
    print(text, file=sys.stdout)
    sys.stdout.flush()


def open_frontend_client():
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

        while True:
            if chrome_p and chrome_p.poll() is not None:
                # chrome has exited, abort!
                log('Restarting due to dead Chrome')
                sys.exit()

            time.sleep(1)
    except (KeyboardInterrupt, SystemExit) as e:
        log("Caught closure exception")
        if chrome_p:
            chrome_p.terminate()


if __name__ == '__main__':
    open_frontend_client()
