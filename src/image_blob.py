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
        print(keypoints)

        return keypoints


if __name__ == '__main__':
    image = cv2.imread('src/img/galaxy8_screenshot_1.png')
    detector = BlobDetector()
    blobs = detector.get_image_blobs(image)
    print(blobs)
