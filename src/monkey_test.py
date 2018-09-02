from time import sleep
from random import randint

from config import configure_logging
from util import measure_task
from device_manager import get_default_device_manager

configure_logging()
device_manager = get_default_device_manager()

'''
Here's a nice performance test for different types of device screenshots.
'''


def measure_screenshot_performance():
    def screenshot_with_writeFile_png(i):
        img = device_manager.device.takeSnapshot()
        img.writeToFile('test_screenshot_%s.png' % (i + 1))

    def screenshot_with_convertToBytes_png(i):
        img = device_manager.device.takeSnapshot()
        bytes = img.convertToBytes('png')

    measure_task(
        screenshot_with_writeFile_png,
        'take screenshot with writeFile png')
    measure_task(screenshot_with_convertToBytes_png,
                 'take screenshot with convertToBytes png')


'''
Here's a nice test to launch the browser and then restart it.
'''


def browser_launch_and_restart():
    print('Launching Browser...')
    device_manager.launch_browser()
    print('Sleeping for 2 seconds, then restarting...')
    sleep(2)
    print('Restarting!')
    device_manager.restart_browser()
    sleep(2)


'''
Here's a nice test to launch the KK:Hollywood app and then restart it.
'''


def hollywood_launch_and_restart():
    print('Launching Hollywood...')
    device_manager.launch_hollywood()
    print('Sleeping for 2 seconds, then restarting...')
    sleep(2)
    print('Restarting!')
    device_manager.restart_hollywood()
    sleep(2)


'''
Here's a nice test to take a few screenshots of the KK:Hollywood app and print their state.
'''


def hollywood_screenshot_loop_test():
    print('Launching Hollywood...')
    device_manager.launch_hollywood()
    print('Sleeping for 20 seconds...')
    sleep(20)

    print('Setting up screenshot loop...')
    for i in range(10):
        filename = device_manager.get_screenshot()
        print('Saved %s' % filename)


'''
Here's a nice test to drag and tap around the screen
'''


def hollywood_drag_and_tap():
    print('Launching Hollywood...')
    device_manager.launch_hollywood()
    print('Sleeping for 5 seconds...')
    sleep(5)

    def drag_x():
        device_manager.drag_delta((randint(50, 500), randint(
            50, 300)), randint(-400, 400), 0, randint(1, 4), randint(10, 200))

    def drag_y():
        device_manager.drag_delta((randint(50, 500), randint(
            50, 300)), 0, randint(-400, 400), randint(1, 4), randint(10, 200))

    def tap():
        device_manager.tap(randint(50, 500), randint(50, 300))

    print('Starting to drag and tap')
    for i in range(100):
        seq = [drag_x, drag_x, drag_x, drag_x]
        for action in seq:
            action()
            sleep(1)


def test():
    # measure_screenshot_performance()
    # browser_launch_and_restart()
    # hollywood_launch_and_restart()
    # hollywood_screenshot_loop_test()
    hollywood_drag_and_tap()


if __name__ == "__main__":
    test()
