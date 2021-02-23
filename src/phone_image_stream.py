'''
Process that:
    1. captures images from vysor
    2. runs image processing
    3. shows annotated images
    4. publishes image state to redis
'''

import time
import json
import numpy as np
import cv2
import mss
import tensorflow as tf
import redis
from darkflow.net.build import TFNet
from PIL import Image

from config import REDIS_HOST, REDIS_PORT, TFNET_CONFIG, IMAGE_PROCESS_SCALE
from config import VYSOR_CAP_AREA, NUM_MONITORS, MONITORS
from kim_logs import get_kim_logger
from ai_state import AIStateProcessor, CURRENT_IMG_CONFIG
from window_setup import setup_vysor_window


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

    def run(self):
        ''' Go! '''
        # Move Vysor window to correct location
        setup_vysor_window()

        # Create Screen Capturer
        sct = mss.mss()

        # Create State Processor
        # This is the most important aspect of the whole project!!!!!!
        processor = AIStateProcessor(image_config=CURRENT_IMG_CONFIG)

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
                captured_np_img = np.array(sct.grab(mon))

                # Get State!
                ai_state = processor.process_from_np_img(sess, captured_np_img, scale=IMAGE_PROCESS_SCALE)

                # Publish to redis (:
                message = {
                    'index': screen_num,
                    'state': ai_state.serialize()
                }
                self.r.publish('phone-image-states', json.dumps(message))

                # Display
                captured_rgb_image = cv2.cvtColor(captured_np_img, cv2.COLOR_BGR2RGB)
                phone_image = Image.fromarray(captured_rgb_image)
                self.r.set('phone-image-data', phone_image.tobytes())

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
