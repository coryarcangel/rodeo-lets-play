import json
import redis
from datetime import datetime
from time import sleep
from config import REDIS_HOST, REDIS_PORT, SECONDS_BETWEEN_BACK_BUTTONS
from config import MAX_NON_KIM_APP_TIME, KK_HOLLYWOOD_PACKAGE
from config import MAX_NO_IMAGE_FEATURES_TIME, MAX_NO_IMAGE_FEATURES_BACK_BUTTON_ATTEMPTS
from config import MAX_BLACK_SCREEN_TIME, MAX_BLACK_SCREEN_BACK_BUTTON_ATTEMPTS
from kim_logs import get_kim_logger
from device_client import DeviceClient


LAUNCHER_PACKAGES = (
    'com.sec.android.app.launcher',
    'com.sec.android.app.sbrowser'
)


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
        self.last_in_game_time = datetime.now()
        self.last_non_black_screen_time = datetime.now()

        self.r = redis.StrictRedis(
            host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

        self.client = DeviceClient(restart_delay=30)
        self.client.start()

    def _get_app_info(self):
        # check if current app is kim
        app_name = ''
        try:
            app_name = self.client.get_cur_process_command()
        except (IndexError) as e:
            # handle deque indexerror in asyncchat
            self.logger.debug(e)
            pass

        is_kim = app_name is None or app_name == '' or app_name == KK_HOLLYWOOD_PACKAGE
        is_launcher = app_name in LAUNCHER_PACKAGES
        return (is_kim, is_launcher)

    def _get_image_state_info(self):
        # decode current image state
        image_state_data_str = self.r.get('cur-phone-image-state')
        image_state_data = json.loads(image_state_data_str) if image_state_data_str is not None else None
        image_state = json.loads(image_state_data['state']) if image_state_data is not None and 'state' in image_state_data else None
        if image_state is None:
            self.logger.debug('no image state...')
            return 0

        pil_features = image_state['pil_features']

        def get_pil_features_info(key):
            f = pil_features[key]
            value = f['value']
            blankspace_is_black = f['blankspace_is_black'] if 'blankspace_is_black' in f else True
            return value, blankspace_is_black

        money, money_blankspace_black = get_pil_features_info('money')
        stars, stars_blankspace_black = get_pil_features_info('stars')

        color_sig = image_state['color_features']['color_sig']
        black_color_sig_str = '0-0-0'
        screen_is_black = black_color_sig_str in color_sig and color_sig.index(black_color_sig_str) == 0

        has_money = money >= 0
        has_stars = stars >= 0
        is_in_game = has_money or has_stars or (money_blankspace_black and stars_blankspace_black)

        self.logger.info('read money, stars, color_sig: %d, %d, %s' % (money, stars, color_sig))

        return {
            'money': money,
            'money_blankspace_black': money_blankspace_black,
            'stars': stars,
            'stars_blankspace_black': stars_blankspace_black,
            'color_sig': color_sig,
            'screen_is_black': screen_is_black,
            'is_in_game': is_in_game
        }

    def _reset_time_counters(self):
        now = datetime.now()
        self.last_in_game_time = now
        self.last_kim_process_time = now
        self.last_non_black_screen_time = now

    def run_monitor_loop(self):
        now = datetime.now()

        image_state_info = self._get_image_state_info()
        is_in_game, screen_is_black = image_state_info['is_in_game'], image_state_info['screen_is_black']
        if is_in_game:
            self.last_in_game_time = now
        if not screen_is_black:
            self.last_non_black_screen_time = now

        is_kim, is_launcher = self._get_app_info()
        if is_kim:
            self.last_kim_process_time = now

        in_game_diff = (now - self.last_in_game_time).seconds
        out_of_game_too_long = in_game_diff >= MAX_NO_IMAGE_FEATURES_TIME
        if in_game_diff > 0:
            self.logger.info('Seconds without image_features: %d' % in_game_diff)

        black_screen_diff = (now - self.last_non_black_screen_time).seconds
        black_screen_too_long = black_screen_diff >= MAX_BLACK_SCREEN_TIME
        if black_screen_diff > 0:
            self.logger.info('Seconds on unknown screen: %d' % black_screen_diff)

        kim_app_diff = (now - self.last_kim_process_time).seconds
        out_of_app_too_long = kim_app_diff >= MAX_NON_KIM_APP_TIME
        if kim_app_diff > 0:
            self.logger.info('Seconds outside app: %d' % kim_app_diff)

        if is_launcher:
            self.logger.info('IN LAUNCHER: GOING TO HOLLYWOOD.')
            self.client.reset_game()
        elif black_screen_too_long:
            # press back N times. if still on black screen, reset
            back_attempts = 0
            while black_screen_too_long and back_attempts < MAX_BLACK_SCREEN_BACK_BUTTON_ATTEMPTS:
                self.logger.info('ON UNKNOWN SCREEN: Pressing back button x%d' % (back_attempts + 1))
                self.client.send_back_button_command()
                sleep(SECONDS_BETWEEN_BACK_BUTTONS)
                black_screen_too_long = self._get_image_state_info()['screen_is_black']
                back_attempts += 1

            if black_screen_too_long:
                self.logger.info('ON UNKNOWN SCREEN: GOING TO HOLLYWOOD.')
                self.client.reset_game()

            self._reset_time_counters()
        elif out_of_game_too_long or out_of_app_too_long:
            # press back N times. if still no image features, reset
            back_attempts = 0
            while (not is_in_game or not is_kim) and back_attempts < MAX_NO_IMAGE_FEATURES_BACK_BUTTON_ATTEMPTS:
                self.logger.info('NO IMAGE FEATURES: Pressing back button x%d' % (back_attempts + 1))
                self.client.send_back_button_command()
                sleep(SECONDS_BETWEEN_BACK_BUTTONS)
                is_in_game = self._get_image_state_info()['is_in_game']
                is_kim, _ = self._get_app_info() if not is_kim else (True, True)
                back_attempts += 1

            if not is_in_game or not is_kim:
                self.logger.info('NO IMAGE FEATURES: Resetting to KK:Hollywood.')
                self.client.reset_game()

            self._reset_time_counters()

        # set last ping time
        self.last_ping_time = datetime.now()
