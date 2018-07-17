import time
import numpy as np
import cv2
import mss
from window import set_window_rect

def show_image_test(x = 0, y = 0, width = 200, height = 200):
    with mss.mss() as sct:
        mon = {'top': y, 'left': x, 'width': width, 'height': height}

        while 'Screen Capturing':
            last_time = time.time()

            # Get raw pixels from the screen, save it to a Numpy array
            img = np.array(sct.grab(mon))

            # Display the picture
            cv2.imshow('OpenCV/Numpy normal', img)

            print('fps: {0}'.format(1 / (time.time()-last_time)))

            # Press "q" to quit
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break


def vysor_show_image_test():
    pos = (0, 0)
    size = (473, 1028)
    set_window_rect('Kim', pos[0], pos[1], size[0], size[1])

    show_image_test(pos[0] + 80, pos[1] + 50, size[0], size[1])


vysor_show_image_test()