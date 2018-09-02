''' Generic Utility Functions '''

import collections
from datetime import datetime

Point = collections.namedtuple("Point", ['x', 'y'])
Rect = collections.namedtuple("Rect", ['x', 'y', 'w', 'h'])


def measure_task(task, label, count=10, print_every_time=False):
    ''' utility for measuring the computation time of given function task,
        which takes index as argument '''
    times = []
    for i in range(count):
        before = datetime.now()
        task(i)
        elapsed = datetime.now() - before
        seconds_elapsed = elapsed.seconds + elapsed.microseconds / 1000000.0
        times.append(seconds_elapsed)
        if print_every_time:
            print('Time to %s: %.3fs' % (label, seconds_elapsed))

    avg_time = sum(times) / float(len(times))
    print('Average time to %s: %.3fs' % (label, avg_time))


def get_rect_center(rect):
    ''' rect is tuple of x,y,w,h '''
    x, y, w, h = rect
    return Point(x + w / 2, y + h / 2)


def floatarr(arr):
    ''' convert array of any to array of floats '''
    return [float(n) for n in arr]


def intarr(arr):
    ''' convert array of any to array of ints '''
    return [int(n) for n in arr]
