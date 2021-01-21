'''
Process that:
    1. captures images from vysor
    2. runs image processing
    3. shows annotated images
    4. publishes image state to redis
'''

import time
import json
import sys
import numpy as np
import cv2
import mss
import tensorflow as tf
import redis
from darkflow.net.build import TFNet
from PIL import Image

from config import REDIS_HOST, REDIS_PORT, TFNET_CONFIG
from config import VYSOR_WINDOW_NAME, VYSOR_RECT, VYSOR_CAP_AREA
from config import WEB_BASED_IMAGE, ANN_TEST, NUM_MONITORS, MONITORS
from kim_logs import get_kim_logger
from ai_state import AIStateProcessor, CURRENT_IMG_CONFIG
from window import setup_vysor_window, set_window_fullscreen
from image_annotation import AnnotatedImageStream


def show_image_test(x=0, y=0, width=200, height=200):
    sct = mss.mss()
    tfnet = TFNet(TFNET_CONFIG)

    mon = {'top': y, 'left': x, 'width': width, 'height': height}

    while 'Screen Capturing':
        last_time = time.time()

        # Get raw pixels from the screen, save it to a Numpy array
        img = np.array(sct.grab(mon))
        img_3chan = img[:, :, :3]

        # Display the picture
        cv2.imshow('OpenCV/Numpy normal', img)

        # Get YOLO results
        yolo_result = tfnet.return_predict(img_3chan)
        print(yolo_result)

        print('fps: {0}'.format(1 / (time.time() - last_time)))

        # Press "q" to quit
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break


def vysor_show_image_test():
    ''' a basic test of capturing from vysor
        and showing the image in opencv '''
    setup_vysor_window()

    x, y, w, h = VYSOR_CAP_AREA
    show_image_test(x, y, w, h)


class VysorDataStream(object):
    ''' runs the process as described in module docs '''

    def __init__(self):
        self.logger = get_kim_logger('VysorDataStream')
        self.r = redis.StrictRedis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=0,
            decode_responses=True)

        self.last_phone_touch = None
        # self.last_phone_touch = {'time': time.time(), 'args': {'object_type': 'Umbrella', 'x': 200, 'y': 200, 'action_prob': 0.2}}

        # Setup Redis Subscription To Handle AI actions
        self.pubsub = self.r.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{
            'ai-phone-touches': self._handle_ai_phone_touch
        })
        self.pubsub.run_in_thread(sleep_time=0.001)

    def _handle_ai_phone_touch(self, message):
        if message['type'] != 'message':
            return

        data = json.loads(message['data'])
        if data:
            self.last_phone_touch = data

    def _get_recent_touch(self, last_time):
        last_phone_touch = self.last_phone_touch
        if last_phone_touch is None:
            return None

        time_diff = last_time - last_phone_touch['time']
        threshold = 1
        # threshold = 10000
        if time_diff > threshold:
            return None  # Ignore older touches

        args = last_phone_touch['args']
        if 'x' not in args or 'y' not in args:
            return None

        label = args['object_type'].lower() if 'object_type' in args else None
        if label is None:
            label = args['type'] if 'type' in args else '?'

        p = (args['x'], args['y'])
        prob = args['action_prob'] if 'action_prob' in args else None
        recent_touch = {'label': label, 'p': p, 'prob': prob}
        return recent_touch

    def run(self):
        ''' Go! '''
        # Move Vysor window to correct location
        setup_vysor_window()

        # Create Screen Capturer
        sct = mss.mss()

        # Create State Processor
        # This is the most important aspect of the whole project!!!!!!
        processor = AIStateProcessor(image_config=CURRENT_IMG_CONFIG)

        annotation_stream = None
        if not WEB_BASED_IMAGE or ANN_TEST:
            # Create ann stream to display the screen captures with opencv
            ann_display_size = (600, 320) if ANN_TEST else (1900, 1000)
            ann_window_name = 'annotations'
            annotation_stream = AnnotatedImageStream(ann_window_name)

            # Move annotation to fullscreen
            set_window_fullscreen(ann_window_name)

        # if more than 1 monitor, we go to the second monitor
        # confusing calc but have to find the "left" pos of 2nd mon for mss
        mon_left = 0 if NUM_MONITORS == 1 else MONITORS[0][1][0]
        all_mon_lefts = [m['left'] for m in sct.monitors]
        mon_num = all_mon_lefts.index(mon_left) if mon_left in all_mon_lefts else 1

        x, y, w, h = VYSOR_CAP_AREA
        mon = {
            'top': y + sct.monitors[mon_num]['top'],
            'left': x + sct.monitors[mon_num]['left'],
            'width': w,
            'height': h,
            'mon': mon_num
        }

        with tf.Session() as sess:
            screen_num = 0
            while 'Screen Capturing':
                last_time = time.time()

                # Get raw pixels from the screen, save it to a Numpy array
                img = np.array(sct.grab(mon))

                # Get State!
                ai_state = processor.process_from_np_img(sess, img)

                # Get Recent Touch
                recent_touch = self._get_recent_touch(last_time)

                # Publish to redis (:
                message = {
                    'index': screen_num,
                    'state': ai_state.serialize(),
                    'recent_touch': recent_touch
                }
                self.r.publish('phone-image-states', json.dumps(message))

                # Display
                if not WEB_BASED_IMAGE or ANN_TEST:
                    annotation_stream.show_image(img, ai_state, recent_touch, display_size=ann_display_size)

                if WEB_BASED_IMAGE:
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    pimg = Image.fromarray(rgb)
                    self.r.set('phone-image-data', pimg.tobytes())

                self.logger.info('fps: {0}'.format(1 / (time.time() - last_time)))

                # increment then Just Give It A Break
                screen_num += 1
                time.sleep(0.001)


def setup_vysor_data_stream():
    ''' runs the process as described in module docs '''
    data_stream = VysorDataStream()
    data_stream.run()


if __name__ == '__main__':
    # vysor_show_image_test()
    setup_vysor_data_stream()
