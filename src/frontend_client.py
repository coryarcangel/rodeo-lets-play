'''
Very simple process that opens chrome to the frontend server url and sets
the window to the proper place
'''

import time
import sys

from config import FRONTEND_WEB_URL, FRONTEND_NAME, NUM_MONITORS, MON_NAMES
import window
from kim_logs import get_kim_logger
from kim_current_app_monitor import KimCurrentAppMonitor


def run_frontend_client():
    """
    Two jobs:
        1. Open chrome to the frontend view, and ensure chrome doesnt die.
        2. Run the KimCurrentAppMonitor loop.
    """

    logger = get_kim_logger('FrontendClient')

    def log(text):
        logger.info(text)

    chrome_p = None
    try:
        log('Opening Chrome to Frontend at {}'.format(FRONTEND_WEB_URL))
        chrome_p = window.open_chrome_url(FRONTEND_WEB_URL, bg=True)

        # ** wait for the chrome to open
        time.sleep(2)

        # ** Move Chrome to the correct place
        mon_name = MON_NAMES[0]
        if NUM_MONITORS >= 2:
            window.set_window_fullscreen(FRONTEND_NAME, mon_name)
        else:
            window.move_window_to_screen(FRONTEND_NAME, 800, 50, 1080, 608, mon_name)
        window.activate_window_by_name(FRONTEND_NAME)

        # ** remove the "chrome didnt shut down correctly"
        win_id = window.get_window_id(FRONTEND_NAME)
        if win_id:
            size = window.get_window_size(win_id)
            window.click_in_window(win_id, size[0] - 20, 80)

        kim_monitor = KimCurrentAppMonitor()

        while True:
            code = chrome_p.poll()
            if chrome_p and code is not None:
                # chrome has exited, abort!
                log('Restarting due to dead Chrome: exit code {}'.format(code))
                sys.exit()

            kim_monitor.run_monitor_loop()

            time.sleep(5)

    except (KeyboardInterrupt, SystemExit) as e:
        log("Caught closure exception")
        if chrome_p:
            chrome_p.terminate()


if __name__ == '__main__':
    run_frontend_client()
