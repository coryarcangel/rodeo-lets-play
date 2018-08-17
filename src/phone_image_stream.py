import time
import json
import numpy as np
import cv2
import mss
import redis
from darkflow.net.build import TFNet
from config import REDIS_HOST, REDIS_PORT
from window import set_window_rect

vysor_rect = (0, 0, 473, 1028)

tfnet_config = {
    'model': 'cfg/yolo.cfg',
    'load': 'bin/yolo.weights',
    'threshold': 0.1
}

def show_image_test(x=0, y = 0, width = 200, height = 200):
    sct = mss.mss()
    tfnet = TFNet(tfnet_config)

    mon = {'top': y, 'left': x, 'width': width, 'height': height}

    while 'Screen Capturing':
        last_time = time.time()

        # Get raw pixels from the screen, save it to a Numpy array
        img = np.array(sct.grab(mon))

        # Display the picture
        cv2.imshow('OpenCV/Numpy normal', img)

        # Get YOLO results
        yolo_result = tfnet.return_predict(img)
        print(yolo_result)

        print('fps: {0}'.format(1 / (time.time()-last_time)))

        # Press "q" to quit
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break

def setup_vysor_window():
    x, y, w, h = vysor_rect
    set_window_rect('Kim', x, y, w, h)

def vysor_show_image_test():
    setup_vysor_window()

    x, y, w, h = vysor_rect
    show_image_test(x + 80, y + 50, w, h)

def setup_vysor_data_stream():
    setup_vysor_window()

    r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

    sct = mss.mss()
    tfnet = TFNet(tfnet_config)

    x, y, w, h = vysor_rect
    mon = {'top': y, 'left': x, 'width': w, 'height': h}

    while 'Screen Capturing':
        last_time = time.time()

        # Get raw pixels from the screen, save it to a Numpy array
        img = np.array(sct.grab(mon))

        # Get YOLO results
        yolo_result = tfnet.return_predict(img)
        r.set('cur_screen_img', json.dumps(yolo_result))

        # Just Give It A Break
        time.sleep(0.001)

vysor_show_image_test()