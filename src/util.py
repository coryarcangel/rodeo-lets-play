''' Generic Utility Functions '''

import collections
import os
import signal
import random
from datetime import datetime
from math import sqrt

Point = collections.namedtuple("Point", ['x', 'y'])
Rect = collections.namedtuple("Rect", ['x', 'y', 'w', 'h'])


def kill_process():
    os.kill(os.getpid(), signal.SIGKILL)


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


def get_noisy_rect_center(rect, noise):
    ''' rect is tuple of x,y,w,h | noise is float 0 -> 1'''
    _, _, w, h = rect
    c = get_rect_center(rect)
    x_var = (-noise * w) + (random.random() * 2 * w * noise)
    y_var = (-noise * h) + (random.random() * 2 * h * noise)
    return Point(c[0] + x_var, c[1] + y_var)


def get_dist_squared(p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    xd, yd = (x0 - x1, y0 - y1)
    return (xd * xd) + (yd * yd)


def get_dist(p0, p1):
    return sqrt(get_dist_squared(p0, p1))


def is_in_rect(point, rect):
    px, py = point
    rx, ry, w, h = rect
    return px >= rx and px <= (rx + w) and py >= ry and py <= (ry + h)


def convert_point_between_rects(point, rect1, rect2):
    ''' convert point from rect1 space to rect2 space '''
    x, y = point
    _, _, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    nx = (w2 / float(w1)) * x + x2
    ny = (h2 / float(h1)) * y + y2
    return (int(nx), int(ny))


def convert_rect_between_rects(rect, rect1, rect2):
    ''' convert rect within rect1 to scaled version space '''
    x, y, w, h = rect
    p = convert_point_between_rects((x, y), rect1, rect2)
    _, _, w1, h1 = rect1
    _, _, w2, h2 = rect2
    width = int((w2 / float(w1)) * w)
    height = int((h2 / float(h1)) * h)
    return (p[0], p[1], width, height)


def floatarr(arr):
    ''' convert array of any to array of floats '''
    return [float(n) for n in arr]


def intarr(arr):
    ''' convert array of any to array of ints '''
    return [int(n) for n in arr]
