''' Module inspired by https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/ '''
import cv2
import imutils
from image_blob import get_center_color

def get_contour_shape(c):
    # approximate the contour
    try:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    except Exception as e:
        print(e)
        return None

    verts = len(approx)
    if verts == 3:
        return "triangle"
    elif len(approx) == 4:
        return 'rectangle'
    else:
        return 'circle'


def get_image_shapes(image):
    # Resize for performance
    resized = imutils.resize(image, width=300)
    ratio = image.shape[0] / float(resized.shape[0])

    # Convert to grayscale, blur, threshold
    resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    resized = cv2.GaussianBlur(resized, (5, 5), 0)
    resized = cv2.threshold(resized, 200, 255, cv2.THRESH_BINARY)[1]

    # cv2.imshow('Threshold', resized)
    # cv2.waitKey(0)

    # find contours
    _, contours, _ = cv2.findContours(resized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def get_shape(c):
        try:
            # Compute center and shape
            M = cv2.moments(c)
            area = M["m00"]
            cX = int((M["m10"] / area) * ratio)
            cY = int((M["m01"] / area) * ratio)

            # Multiply contour by ratio and draw on image
            rc = (c.astype('float') * ratio).astype('int')

            color, dom_color = get_center_color(image, (cX, cY))
            return {
                'shape': get_contour_shape(c),
                'point': (cX, cY),
                'area': area * ratio,
                'color': color,
                'dom_color': dom_color,
                'contour': rc
            }
        except Exception as e:
            print(e)
            return None

    shapes = [get_shape(c) for c in contours]

    return [s for s in shapes if s and s['shape']]


def draw_shapes(image, shapes):
    for shape in shapes:
        cv2.drawContours(image, [shape['contour']], -1, (0, 255, 0), 2)
        cv2.putText(image, shape['shape'], shape['point'], cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 255, 255), 2)

    cv2.imshow('Shapes', image)
    cv2.waitKey(0)


if __name__ == '__main__':
    image = cv2.imread('src/img/galaxy8_screenshot_1.png')
    shapes = get_image_shapes(image)
    print([(shape, p) for shape, p, _ in shapes])

    # draw_shapes(image, shapes)
