import json
import redis
from datetime import datetime
from time import sleep
from config import REDIS_HOST, REDIS_PORT, SECONDS_BETWEEN_BACK_BUTTONS
from config import MAX_NON_KIM_APP_TIME, KK_HOLLYWOOD_PACKAGE
from config import MAX_NO_MONEY_READ_TIME, MAX_NO_MONEY_READ_BACK_BUTTON_ATTEMPTS, MAX_BLACK_SCREEN_TIME
from kim_logs import get_kim_logger
from device_client import DeviceClient


LAUNCHER_PACKAGE = 'com.sec.android.app.launcher'


class KimCurrentAppMonitor(object):
    """
    not sure exactly where to put this code, but it is supposed to ensure we inside
    the main part of the game. does through two ways:
        1. checks that we have been able to read money recently.
        if not, we try some back buttons and finally a reset.
        this is supposed to handle in-game browser, ads, facebook, things like that.
        2. pings monkeyrunner sometimes to ensure that the phone stays
           in the kim hollywood app (attempts to handle ad clicks, phone sleep, etc)
        2.5 same screen logic is handled in ai_heuristic for now...
    """

    def __init__(self):
        self.logger = get_kim_logger('AppMonitor')
        self.last_ping_time = datetime.now()
        self.last_kim_process_time = datetime.now()
        self.last_money_time = datetime.now()
        self.last_non_black_screen_time = datetime.now()
        self.max_non_kim_time = MAX_NON_KIM_APP_TIME
        self.max_no_money_time = MAX_NO_MONEY_READ_TIME
        self.max_back_attempts = MAX_NO_MONEY_READ_BACK_BUTTON_ATTEMPTS
        self.max_black_screen_time = MAX_BLACK_SCREEN_TIME

        self.r = redis.StrictRedis(
            host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

        self.client = DeviceClient()
        self.client.start()

    def _get_app_is_kim(self):
        # check if current app is kim
        app_name = ''
        try:
            app_name = self.client.get_cur_process_command()
        except (IndexError) as e:
            # handle deque indexerror in asyncchat
            self.logger.debug(e)
            pass

        is_kim = app_name is None or app_name == '' or app_name == KK_HOLLYWOOD_PACKAGE
        is_launcher = app_name == LAUNCHER_PACKAGE
        return (is_kim, is_launcher)

    def _get_money(self):
        # decode current image state
        image_state_data_str = self.r.get('cur-phone-image-state')
        image_state_data = json.loads(image_state_data_str) if image_state_data_str is not None else None
        image_state = json.loads(image_state_data['state']) if image_state_data is not None and 'state' in image_state_data else None
        if image_state is None:
            self.logger.debug('no image state...')
            return 0

        money = image_state['money']
        self.logger.info('read money: %d' % money)

        color_sig = image_state['color_features']['color_sig']
        black_color_sig_str = '0-0-0'
        black_is_dom_color = black_color_sig_str in color_sig and color_sig.index(black_color_sig_str) == 0
        self.logger.info('read color_sig: %s' % color_sig)

        return (money, color_sig, black_is_dom_color)

    def run_monitor_loop(self):
        now = datetime.now()

        money, color_sig, black_is_dom_color = self._get_money()
        if money >= 0:
            self.last_money_time = now
        if not black_is_dom_color:
            self.last_non_black_screen_time = now

        is_kim, is_launcher = self._get_app_is_kim()
        if is_kim:
            self.last_kim_process_time = now

        money_diff = (now - self.last_money_time).seconds
        money_too_long = money_diff >= self.max_no_money_time
        if money_diff > 0:
            self.logger.info('Seconds without money: %d' % money_diff)

        black_screen_diff = (now - self.last_non_black_screen_time).seconds
        black_screen_too_long = black_screen_diff >= self.max_black_screen_time
        if black_screen_diff > 0:
            self.logger.info('Seconds on unknown screen: %d' % black_screen_diff)

        kim_app_diff = (now - self.last_kim_process_time).seconds
        kim_too_long = kim_app_diff >= self.max_non_kim_time
        if kim_app_diff > 0:
            self.logger.info('Seconds outside app: %d' % kim_app_diff)

        if is_launcher:
            self.logger.info('IN LAUNCHER: GOING TO HOLLYWOOD.')
            self.client.reset_game()
        elif black_screen_too_long:
            self.logger.info('ON UNKNOWN SCREEN: GOING TO HOLLYWOOD.')
            self.client.reset_game()
        elif money_too_long or kim_too_long:
            # press back N times. if still no money, reset
            back_attempts = 0
            while money < 0 and back_attempts < self.max_back_attempts:
                self.logger.info('NO MONEY: Pressing back button x%d' % (back_attempts + 1))
                self.client.send_back_button_command()
                sleep(SECONDS_BETWEEN_BACK_BUTTONS)
                money, _, _ = self._get_money()
                back_attempts += 1

            if money < 0:
                self.logger.info('NO MONEY: Resetting to KK:Hollywood.')
                self.client.reset_game()

            # restart counter
            self.last_money_time = now
            self.last_kim_process_time = now
            self.last_non_black_screen_time = now

        # set last ping time
        self.last_ping_time = now
