''' Simple set of commands for moving os windows around '''

import subprocess
import time
from config import SCREEN_SIZES


def run_cmd(cmd):
    ''' run shell command as subprocess '''
    return subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE).communicate()[0]


def run_cmd_bg(cmd):
    ''' run shell command as background process '''
    return subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE)


def set_window_pos(win_id, x, y):
    ''' sets position of window with given id '''
    return run_cmd('xdotool windowmove {} {} {}'.format(win_id, x, y))


def get_window_size(win_id):
    ''' gets size of window with given id '''
    lines = run_cmd('xdotool getwindowgeometry {}'.format(win_id)).strip().decode('UTF-8').split('\n')
    size = [l.split(': ')[1] for l in lines if 'Geometry:' in l][0]
    width, height = [int(x) for x in size.split('x')]
    return (width, height)


def set_window_size(win_id, width, height):
    ''' sets size of window with given id '''
    return run_cmd('xdotool windowsize {} {} {}'.format(win_id, width, height))


def get_window_id(name):
    ''' gets xdotool window id for window with given name '''
    return run_cmd(
        "xdotool search --onlyvisible --name {}".format(name)).strip().decode('UTF-8')


def activate_window(win_id):
    if win_id:
        run_cmd('xdotool windowactivate {}'.format(win_id))


def activate_window_by_name(name):
    win_id = get_window_id(name)
    activate_window(win_id)


def click_in_window(win_id, x, y):
    ''' moves rect with given win_id to specified location and size '''
    if win_id:
        activate_window(win_id)
        run_cmd('xdotool mousemove --window {} {} {}'.format(win_id, x, y))
        run_cmd('xdotool click 1')


def open_chrome_url(url, fullscreen=True, bg=True):
    ''' opens chrome window / tab to given url
    https://kapeli.com/cheat_sheets/Chromium_Command_Line_Switches.docset/Contents/Resources/Documents/index
    '''
    cmd = 'google-chrome {} --new-window {}'.format(
        '--start-fullscreen' if fullscreen else '', url)
    return run_cmd_bg(cmd) if bg else run_cmd(cmd)


def move_window_to_screen(name, x, y, width, height, scr='DP-1'):
    '''
    moves window to given size on given monitor
    https://askubuntu.com/questions/702071/move-windows-to-specific-screens-using-the-command-line
    list screens like so: xrandr --query
    '''
    # just a helper function, to reduce the amount of code
    def get(cmd):
        return subprocess.check_output(cmd).decode("utf-8")

    # get the data on all currently connected screens, their x-resolution
    screendata = [l.split() for l in get(["xrandr"]).splitlines() if " connected" in l]
    screen_left_positions = sum([
        [(w[0], s.split("+")[-2]) for s in w if s.count("+") == 2]
        for w in screendata], [])

    def get_window_class(classname):
        # function to get all windows that belong to a specific window class (application)
        w_list = [l.split()[0] for l in get(["wmctrl", "-l"]).splitlines()]
        return [w for w in w_list if classname in get(["xprop", "-id", w])]

    try:
        # determine the left position of the targeted screen (x)
        pos = [sc for sc in screen_left_positions if sc[0] == scr][0]
    except IndexError:
        # warning if the screen's name is incorrect (does not exist)
        print(scr, "does not exist. Check the screen name")
    else:
        for w in get_window_class(name):
            # first move and resize the window, to make sure it fits completely
            # inside the targeted screen else the next command will fail...
            subprocess.Popen(["wmctrl", "-ir", w, "-e", "0," + str(int(pos[1]) + x) + "," + str(y) + ",300,300"])
            time.sleep(0.2)
            # maximize the window on its new screen
            subprocess.Popen(["xdotool", "windowsize", w, str(width), str(height)])


def set_window_fullscreen(name, scr='DP-1'):
    ''' moves window to fullscreen on given monitor '''
    size = SCREEN_SIZES[scr] if scr in SCREEN_SIZES else (1920, 1080)
    move_window_to_screen(name, 0, 0, size[0], size[1], scr)
