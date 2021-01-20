import sys
from datetime import datetime

from device_client import DeviceClient

KK_HOLLYWOOD_PACKAGE = 'com.glu.stardomkim'


def log(text):
    print(text, file=sys.stdout)
    sys.stdout.flush()


class KimCurrentAppMonitor(object):
    """
    not sure exactly where to put this code, but it pings monkeyrunner sometimes
    to ensure that the phone stays in the kim hollywood app as often as possible
    (attempts to handle ad clicks, phone sleep, etc)
    same screen logic is handled in ai_heuristic for now...
    """

    def __init__(self):
        self.last_ping_time = datetime.now()
        self.last_kim_process_time = datetime.now()
        self.max_non_kim_time = 25  # 25 seconds until we force a reset.

        self.client = DeviceClient()
        self.client.start()

    def run_monitor_loop(self):
        now = datetime.now()

        # check if current app is kim
        app_name = self.client.get_cur_process_command()
        is_kim = app_name is None or app_name == '' or app_name == KK_HOLLYWOOD_PACKAGE
        if is_kim:
            self.last_kim_process_time = now

        # check if reset is necessary
        diff = now - self.last_kim_process_time
        if diff.seconds >= self.max_non_kim_time:
            # reset to kim app.
            log('kim app monitor is resetting to kim.')
            self.client.reset_game()
            self.last_kim_process_time = now

        self.last_ping_time = now
