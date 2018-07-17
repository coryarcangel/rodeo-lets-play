import subprocess

def run_cmd(cmd):
    return subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE).communicate()[0]

def set_window_pos(win_id, x, y):
    return run_cmd('xdotool windowmove {} {} {}'.format(win_id, x, y))

def set_window_size(win_id, width, height):
    return run_cmd('xdotool windowsize {} {} {}'.format(win_id, width, height))

def set_window_rect(name, x, y, width, height):
    win_id = run_cmd("xdotool search --onlyvisible --name {}".format(name))
    if not win_id:
        return None

    set_window_pos(win_id, x, y)
    set_window_size(win_id, width, height)