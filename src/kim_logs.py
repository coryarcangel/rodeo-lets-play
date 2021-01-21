import logging
import os
import sys

is_process_hub = os.environ.get('PROCESS_HUB') is not None
log_level = logging.DEBUG

""" Old log function used in:
frontend_client, sever, cur_app_monitor, phone_image_stream """
# def log(text):
#     print(text, file=sys.stdout)
#     sys.stdout.flush()


class KimLogs():
    def __init__(self):
        self.configure_logging()

    def configure_logging(self):
        # format = '%(asctime)s.%(msecs)03d:%(levelname)s:%(name)s:%(message)s'
        format = '%(message)s' if is_process_hub \
            else '%(asctime)s:%(levelname)s:%(name)s - %(message)s'
        logging.basicConfig(
            stream=sys.stdout,
            format=format,
            level=log_level,
            datefmt='%Y-%m-%d %H:%M:%S')

    def get_kim_logger(self, name):
        return logging.getLogger(name)


kl = KimLogs()


def get_kim_logger(name):
    return kl.get_kim_logger(name)
