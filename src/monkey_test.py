import os
from time import sleep
from util import measure_task
from device_manager import get_default_device_manager

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


def test():
    # measure_screenshot_performance()
    # browser_launch_and_restart()
    # hollywood_launch_and_restart()
    hollywood_screenshot_loop_test()


if __name__ == "__main__":
    test()
