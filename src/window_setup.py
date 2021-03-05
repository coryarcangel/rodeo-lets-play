import sys
from config import VYSOR_WINDOW_NAME, VYSOR_RECT, FRONTEND_NAME, CHROME_ERROR_X_OFFSET
from config import NUM_MONITORS, MONITORS, MON_NAMES, DASHBOARD_NAME, SHOW_FRONTEND
import window


def setup_process_hub_window():
    win_name = DASHBOARD_NAME
    if NUM_MONITORS == 1:
        w = int(1920 / 2)
        x, y, h = (1920 - w, 0, 1080)
        window.move_window_to_screen(win_name, x, y, w, h, MON_NAMES[0])
    elif NUM_MONITORS == 2:
        # share with vysor area
        x = VYSOR_RECT[0] + VYSOR_RECT[2]
        y, w, h = (0, 1920 - x, 1080)
        window.move_window_to_screen(win_name, x, y, w, h, MON_NAMES[1])
    elif NUM_MONITORS == 3:
        # fullscreen!
        window.set_window_fullscreen(win_name, MON_NAMES[2])


def click_in_process_hub_window():
    dashboard_id = window.get_window_id(DASHBOARD_NAME)
    if dashboard_id:
        window.click_in_window(dashboard_id, 20, 20)


def setup_vysor_window():
    ''' Moves the Vysor window to fixed location for capture via mss '''
    x, y, w, h = VYSOR_RECT
    mon_name, _ = MONITORS[1 if NUM_MONITORS >= 2 else 0]
    window.move_window_to_screen(VYSOR_WINDOW_NAME, x, y, w, h, mon_name)
    window.activate_window_by_name(VYSOR_WINDOW_NAME)

    # remove mouse from vysor
    click_in_process_hub_window()


def setup_frontend_window():
    # ** Move Chrome to the correct place
    if not SHOW_FRONTEND:
        return

    fullscreen = NUM_MONITORS >= 2
    mon_name = MON_NAMES[0]
    if fullscreen:
        window.set_window_fullscreen(FRONTEND_NAME, mon_name)
    else:
        window.move_window_to_screen(FRONTEND_NAME, 800, 50, 1080, 608, mon_name)
    window.activate_window_by_name(FRONTEND_NAME)

    # ** remove the "chrome didnt shut down correctly"
    win_id = window.get_window_id(FRONTEND_NAME)
    if win_id:
        size = window.get_window_size(win_id)
        x, y = CHROME_ERROR_X_OFFSET
        window.click_in_window(win_id, size[0] - x, y)


def setup_visible_windows(arg):
    if arg == 'all' or arg == 'vysor':
        setup_vysor_window()
    if arg == 'all' or arg == 'process_hub':
        setup_process_hub_window()
    if arg == 'all' or arg == 'frontend':
        setup_frontend_window()

    # click in dashboard to hide mouse from frontend
    click_in_process_hub_window()
    window.activate_window_by_name(FRONTEND_NAME)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else 'all'
    setup_visible_windows(arg)
