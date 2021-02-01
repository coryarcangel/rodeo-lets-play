import json
import redis
from time import time
from kim_logs import get_kim_logger
from ai_actions import get_action_type_str
from config import REDIS_HOST, REDIS_PORT


class AIInfoPublisher:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.logger = get_kim_logger('AIActionPublisher')

        self.logger.debug('Connecting to %s:%d', host, port)
        self.r = redis.StrictRedis(
            host=host, port=port, db=0, decode_responses=True)

    def publish_data(self, channel, data, tojson=True):
        self.r.publish(channel, json.dumps(data) if tojson else data)

    def publish_action(self, action, args):
        name = get_action_type_str(action)
        ad = {'type': name, 'time': time(), 'args': args}
        ad['label'] = args['object_type'] if 'object_type' in args else name
        if 'action_prob' in args:
            ad['prob'] = args['action_prob']
        if 'x' in args and 'y' in args:
            ad['p'] = [args['x'], args['y']]
        self.publish_data('ai-action-stream', ad)

    def publish_status(self, ai_status):
        self.publish_data('ai-status-updates', ai_status)

    def publish_log_lines(self, lines):
        for line in lines:
            self.publish_data('ai-log-lines', line, tojson=False)


publishers_by_name = {}


def get_ai_info_publisher(host=REDIS_HOST, port=REDIS_PORT):
    name = str(REDIS_HOST) + ':' + str(port)
    if name not in publishers_by_name:
        publishers_by_name[name] = AIInfoPublisher(host=host, port=port)
    return publishers_by_name[name]
