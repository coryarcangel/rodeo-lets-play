""" Code to transform images from KK:Hollywood into numerical state """

import tesserocr
import time
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from concurrent import futures
from image_color import get_image_color_sig
from tess_test import detect


TESTING = False
TESTING_BLANKSPACE = False


def read_num_from_img(image):
    """ Performs OCR on image and converts text to number """
    # text = tesserocr.image_to_text(image).strip()
    text = detect( np.array(image.convert('RGB')) )
    try:
        f = filter(str.isdigit, text.encode('ascii', 'ignore').decode('utf-8'))
        t = ''.join(f)
        if len(t) == 0:
            return -1
        val = int(t)
        return val
    except BaseException:
        return -1


class ImageOCRProcessor(object):
    """ Helps with reading characters from gameplay images """

    def __init__(self, image_config):
        self.image_config = image_config

    def _read_hud_value(self, image, left):
        padding = self.image_config.top_menu_padding
        height = self.image_config.top_menu_height
        width = self.image_config.top_menu_item_width
        item_crop_box = (left, padding, left + width, height - padding)
        hud_image = image.crop(item_crop_box)
        # hud_image = ImageEnhance.Contrast(hud_image).enhance(2)
        # hud_image = ImageEnhance.Sharpness(hud_image).enhance(4)
        # hud_image = ImageOps.grayscale(hud_image)
        # hud_image = hud_image.resize((width*2, (height-padding*2)*2), Image.ANTIALIAS)
        # hud_image = hud_image.resize((162,100), Image.ANTIALIAS)
        value = read_num_from_img(hud_image)
        if TESTING:
            new_im.show()
            print(value)
            time.sleep(10)
        return value

    def _get_blankspace_is_black(self, image, left):
        left_pad, top, width, height = self.image_config.blankspace_rect
        item_crop_box = (left + left_pad, top, left + width, top + height)
        cropped_image = image.crop(item_crop_box)
        np_cropped_image = np.array(cropped_image)
        blankspace_color_sig = get_image_color_sig(np_cropped_image[:, :, :3], k=1, squash_factor=0.15)
        black = '0-0-0'
        blankspace_is_black = black in blankspace_color_sig and blankspace_color_sig.index(black) == 0
        if TESTING_BLANKSPACE:
            print(np_cropped_image.shape)
            print(left, blankspace_color_sig, blankspace_is_black)
            cropped_image.resize((200, 130)).show()
            time.sleep(20)
        return blankspace_is_black

    def get_hud_features(self, image, left, calc_blankspace):
        value = self._read_hud_value(image, left)
        return value

    def process_image(self, image):
        '''
            FPS with no text reading: ~7.5
            FPS with straight sync text reading: ~3.0
            FPS with thread pool text reading: ~3.9
        '''
        # Get shape
        width, height = image.size
        image_shape = (width, height, 3)

        # get OCR text from known HUD elements
        values = {'image_shape': image_shape}

        with futures.ThreadPoolExecutor() as executor:
            future_to_key = {
                executor.submit(self.get_hud_features, image, self.image_config.money_item_left, True): 'money',
                executor.submit(self.get_hud_features, image, self.image_config.stars_item_left, False): 'stars',
                # executor.submit(self._read_hud_value, image, self.image_config.bolts_item_left): 'bolts',
            }
            for future in futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    values[key] = future.result()
                except Exception as e:
                    print('Exception reading value: %s', e)

        return values

    def process_filename(self, filename):
        image = Image.open(filename).convert('RGB')
        return self.process_image(image)

    def process_np_img(self, np_img):
        image = Image.fromarray(np_img).convert('RGB')
        return self.process_image(image)
