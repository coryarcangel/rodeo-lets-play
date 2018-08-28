''' Simple set of commands for moving os windows around '''

import subprocess


def run_cmd(cmd):
    ''' run shell command as subprocess '''
    return subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE).communicate()[0]


def set_window_pos(win_id, x, y):
    ''' sets position of window with given id '''
    return run_cmd('xdotool windowmove {} {} {}'.format(win_id, x, y))


def set_window_size(win_id, width, height):
    ''' sets size of window with given id '''
    return run_cmd('xdotool windowsize {} {} {}'.format(win_id, width, height))


def set_window_rect(name, x, y, width, height):
    ''' moves rect with given name to specified location and size '''
    win_id = run_cmd(
        "xdotool search --onlyvisible --name {}".format(name)).strip().decode('UTF-8')
    if not win_id:
        return

    set_window_pos(win_id, x, y)
    set_window_size(win_id, width, height)
