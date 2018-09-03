""" Code to transform images from KK:Hollywood into numerical state """

import tesserocr
from PIL import Image
from concurrent import futures


def read_num_from_img(image):
    """ Performs OCR on image and converts text to number """
    text = tesserocr.image_to_text(image).strip()
    try:
        f = filter(str.isdigit, text.encode('ascii', 'ignore').decode('utf-8'))
        t = ''.join(f)
        val = int(t)
        return val
    except BaseException:
        return 0


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
        value = read_num_from_img(hud_image)
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
                executor.submit(self._read_hud_value, image, self.image_config.money_item_left): 'money',
                executor.submit(self._read_hud_value, image, self.image_config.stars_item_left): 'stars'
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
