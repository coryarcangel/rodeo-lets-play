from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from time import sleep
from util import measure_task
from device import DeviceManager

# Connects to the current device, returning a MonkeyDevice object
# the first argument is a timeout in seconds
# the second argument is a regular expression describing the device ID (all can be found with "adb devices" command) - it can be left blank
print('Connecting to device...')
device = MonkeyRunner.waitForConnection(10, 'emulator-\d+')
device_manager = DeviceManager(device)
print('Connected!')
print('device name: %s' % device.getProperty('build.product'))
print('device size: %sx%s' % (device.getProperty('display.width'), device.getProperty('display.height')))

'''
Here's a nice performance test for different types of device screenshots.
'''
def measure_screenshot_performance():
    def screenshot_with_writeFile_png(i):
        img = device.takeSnapshot()
        img.writeToFile('test_screenshot_%s.png' % (i + 1))

    def screenshot_with_convertToBytes_png(i):
        img = device.takeSnapshot()
        bytes = img.convertToBytes('png')

    measure_task(screenshot_with_writeFile_png, 'take screenshot with writeFile png')
    measure_task(screenshot_with_convertToBytes_png, 'take screenshot with convertToBytes png')

'''
Here's a nice test to launch the browser and then restart it.
'''
def browser_launch_and_restart():
    print('Launching Browser...')
    device_manager.launch_browser()
    print('Sleeping for 10 seconds, then restarting...')
    sleep(2)
    print('Restarting!')
    device_manager.restart_browser()
    sleep(2)

def test():
    # measure_screenshot_performance()
    browser_launch_and_restart()

if __name__ == "__main__":
    test()
