'''
Very simple process that opens chrome to the frontend server url and sets
the window to the proper place
'''

import time
import traceback
import signal
import sys

from config import FRONTEND_WEB_URL, NUM_MONITORS, SHOW_FRONTEND
import window
from window_setup import setup_frontend_window
from kim_logs import get_kim_logger
from kim_current_app_monitor import KimCurrentAppMonitor
from util import kill_process


def run_frontend_client():
    """
    Two jobs:
        1. Open chrome to the frontend view, and ensure chrome doesnt die.
        2. Run the KimCurrentAppMonitor loop.
    """

    logger = get_kim_logger('FrontendClient')
    chrome_p = None

    def log(text):
        logger.info(text)

    def graceful_exit():
        log('Gracefully exiting...')
        if chrome_p:
            chrome_p.terminate()
        window.kill_chrome()
        sys.exit(0)

    def signal_handler(sig, frame):
        graceful_exit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if SHOW_FRONTEND:
            window.kill_chrome()

            log('Opening Chrome to Frontend at {}'.format(FRONTEND_WEB_URL))
            fullscreen = NUM_MONITORS >= 2
            chrome_p = window.open_chrome_url(FRONTEND_WEB_URL, fullscreen=fullscreen, bg=True)

        # ** wait for the chrome to open
        time.sleep(2)

        setup_frontend_window()

        log('Starting Monitor Loop in 20 seconds...')
        time.sleep(20)
        kim_monitor = KimCurrentAppMonitor()

        while True:
            if SHOW_FRONTEND:
                code = chrome_p.poll()
                if chrome_p and code is not None:
                    # chrome has exited, abort!
                    log('Restarting due to dead Chrome: exit code {}'.format(code))
                    sys.exit()

            kim_monitor.run_monitor_loop()

            time.sleep(5)

    except (KeyboardInterrupt, SystemExit, Exception) as e:
        log("Caught closure exception")
        log(e)
        traceback.print_exc()
        graceful_exit()


if __name__ == '__main__':
    try:
        run_frontend_client()
    except Exception:
        traceback.print_exc()
        kill_process()
