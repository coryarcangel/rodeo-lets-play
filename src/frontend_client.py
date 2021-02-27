'''
Very simple process that opens chrome to the frontend server url and sets
the window to the proper place
'''

import time
import sys

from config import FRONTEND_WEB_URL, NUM_MONITORS
import window
from window_setup import setup_frontend_window
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
        fullscreen = NUM_MONITORS >= 2
        chrome_p = window.open_chrome_url(FRONTEND_WEB_URL, fullscreen=fullscreen, bg=True)

        # ** wait for the chrome to open
        time.sleep(2)

        setup_frontend_window()

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
        log(e)
        if chrome_p:
            chrome_p.terminate()


if __name__ == '__main__':
    run_frontend_client()
