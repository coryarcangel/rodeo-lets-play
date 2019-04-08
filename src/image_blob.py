''' Module inspired by:
    * https://www.learnopencv.com/blob-detection-using-opencv-python-c/
    * https://stackoverflow.com/questions/42924059/detect-different-color-blob-opencv
'''
import cv2


class BlobDetector(object):
    """Uses opencv blob detection to find solid-color potentially actionable
    blobs in image."""

    def __init__(self, set_params=None):
        # Setup SimpleBlobDetector parameters.
        params = cv2.SimpleBlobDetector_Params()

        # Change thresholds
        params.minThreshold = 10
        params.maxThreshold = 200

        # Filter by Area.
        params.filterByArea = True
        params.minArea = 100

        # Filter by Circularity
        params.filterByCircularity = True
        params.minCircularity = 0.1

        # Filter by Convexity
        params.filterByConvexity = True
        params.minConvexity = 0.87

        # Filter by Inertia
        params.filterByInertia = True
        params.minInertiaRatio = 0.01

        if set_params:
            set_params(params)

        self.detector = cv2.SimpleBlobDetector_create(params)

    def get_image_blobs(self, image):
        """ pass an alpha-less numpy image, get some blobs """

        keypoints = self.detector.detect(image)

        colored_points = [{'point': (int(k.pt[0]), int(k.pt[1])), 'size': k.size} for k in keypoints]
        for c in colored_points:
            x, y = c['point']
            color = image[x, y]
            g, r, b = color
            dom_color = 'white'
            if g > r and g > b:
                dom_color = 'green'
            elif r > g and r > b:
                dom_color = 'red'
            elif b > g and b > r:
                dom_color = 'blue'
            elif b < 100 and r < 100 and g < 100:
                dom_color = 'black'
            else:
                pass

            c['color'] = color
            c['dom_color'] = dom_color

        return colored_points


if __name__ == '__main__':
    image = cv2.imread('src/img/galaxy8_screenshot_1.png')
    detector = BlobDetector()
    blobs = detector.get_image_blobs(image)
    print(blobs)
