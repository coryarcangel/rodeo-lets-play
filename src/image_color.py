''' Module inspired by https://adamspannbauer.github.io/2018/03/02/app-icon-dominant-colors/ '''
from sklearn.cluster import KMeans
from collections import Counter
import cv2
from config import COLOR_SIG_K, COLOR_SIG_PCT_FACTOR, COLOR_SIG_SQUASH_FACTOR


def get_img_hash(image, hash_size=8):
    # https://www.pyimagesearch.com/2017/11/27/image-hashing-opencv-python/

    # resize the input image, adding a single column (width) so we
    # can compute the horizontal gradient
    resized = cv2.resize(image, (hash_size + 1, hash_size))
    resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)  # convert 2 gray

    # compute the (relative) horizontal gradient between adjacent column pixels
    diff = resized[:, 1:] > resized[:, :-1]

    # convert the difference image to a hash
    return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])


def get_img_dom_colors(image, k=3, image_processing_size=None):
    """
    takes an image as input (no alpha channel!)
    returns the dominant colors of the image as a list

    dominant color is found by running k means on the
    pixels & returning the centroid of the largest cluster

    processing time is sped up by working with a smaller image;
    this resizing can be done with the image_processing_size param
    which takes a tuple of image dims as input

    >>> get_dominant_color(my_image, k=4, image_processing_size = (25, 25))
    [56.2423442, 34.0834233, 70.1234123]
    """

    # if no new dims provided, force 40w image
    if image_processing_size is None:
        h, w, _ = image.shape
        r = float(w) / h
        image_processing_size = (40, int(40 / r))

    # resize image
    image = cv2.resize(image, image_processing_size, interpolation=cv2.INTER_AREA)

    # reshape the image to be a list of pixels
    image = image.reshape((image.shape[0] * image.shape[1], 3))

    # cluster and assign labels to the pixels
    clt = KMeans(n_clusters=k)
    labels = clt.fit_predict(image)

    # count labels to find most popular
    label_counts = Counter(labels)
    common = label_counts.most_common(k)

    total = float(sum([l[1] for l in common]))
    color_counts = [(clt.cluster_centers_[label], count / total, count) for label, count in common]

    return color_counts


def get_image_color_sig_component(color,
                                  pct,
                                  pct_factor=COLOR_SIG_PCT_FACTOR,
                                  squash_factor=COLOR_SIG_SQUASH_FACTOR):
    spct = int(pct * pct_factor * 100)  # get simplified version of pct
    squashed = [int(f * squash_factor) for f in color]  # get simplified version of r,g,b
    sig_comp = '-'.join([str(f) for f in squashed] + [str(spct)])
    return sig_comp


def get_image_color_sig(image,
                        k=COLOR_SIG_K,
                        image_processing_size=None,
                        pct_factor=COLOR_SIG_PCT_FACTOR,
                        squash_factor=COLOR_SIG_SQUASH_FACTOR):
    """ get color sig !! """
    dom_colors = get_img_dom_colors(image, k, image_processing_size)

    sig_components = [get_image_color_sig_component(color, pct, pct_factor, squash_factor) for color, pct, _ in dom_colors]
    sig_components.sort()
    return '__'.join(sig_components)


def get_image_color_features(image, k=COLOR_SIG_K, image_processing_size=None):
    """
    get color features !!
    """

    color_sig = get_image_color_sig(image, k, image_processing_size)
    image_sig = get_img_hash(image)

    return {
        # 'dom_colors': dom_colors,
        'color_sig': color_sig,
        'image_sig': image_sig
    }


if __name__ == '__main__':
    image = cv2.imread('src/img/galaxy8_screenshot_1.png')
    color_features = get_image_color_features(image)
    print(color_features)
























































