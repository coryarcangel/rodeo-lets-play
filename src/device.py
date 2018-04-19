""" DeviceManager class to control an Android emulator or phone """

import logging
from time import sleep
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice #pylint: disable=E0401

### Constants
BROWSER_PACKAGE = 'com.android.chrome'
BROWSER_COMPONENT = '%s/com.google.android.apps.chrome.Main' % BROWSER_PACKAGE

KK_HOLLYWOOD_PACKAGE = 'com.glu.stardomkim'
KK_HOLLYWOOD_COMPONENT = '%s/com.google.android.vending.expansion.downloader_impl.DownloaderActivity' % KK_HOLLYWOOD_PACKAGE

class DeviceManager(object):
    '''
    Wrapper around MonkeyDevice with some higher-level controls.
    '''

    def __init__(self, device):
        self.device = device
        self.frame_count = 0
        self.logger = logging.getLogger('DeviceManager')

    def log_info(self):
        """ Logs information about the connected device """
        self.logger.debug('device name: %s', self.device.getProperty('build.product'))
        self.logger.debug('device size: %sx%s', self.device.getProperty('display.width'), self.device.getProperty('display.height'))

    # component must be in the form: `PACKAGE_NAME/MAIN_ACTIVITY_NAME`
    def _launch_app(self, component):
        categories = ['android.intent.category.LAUNCHER']
        self.device.startActivity(component=component, categories=categories)

    def _restart_app(self, package, component):
        # simulate home press to return to menu
        self.device.press('KEYCODE_HOME', MonkeyDevice.DOWN_AND_UP)

        # kill the package
        self.device.shell('am force-stop %s' % package)

        # launch the app
        self._launch_app(component)

    def launch_browser(self):
        """ Launches Google Chrome """
        self._launch_app(BROWSER_COMPONENT)

    def restart_browser(self):
        """ Restarts Google Chrome """
        self._restart_app(BROWSER_PACKAGE, BROWSER_COMPONENT)

    def launch_hollywood(self):
        """ Launches the KK:Hollywood app """
        self._launch_app(KK_HOLLYWOOD_COMPONENT)

    def restart_hollywood(self):
        """ Restarts the KK:Hollywood app """
        self._restart_app(KK_HOLLYWOOD_PACKAGE, KK_HOLLYWOOD_COMPONENT)

    def reset_hollywood(self):
        """ Restarts the KK:Hollywood app, and waits until game is playable """
        self.restart_hollywood()
        sleep(5)

    def get_screenshot(self):
        """ Calls save_screenshot with an auto-incrementing filename """
        filename = 'current_screen_%s.png' % self.frame_count
        self.frame_count += 1
        return self.save_screenshot(filename)

    def save_screenshot(self, filename):
        """ Takes screenshot of current state of device and saves to given filename """
        img = self.device.takeSnapshot()
        img.writeToFile(filename)
        return filename

def get_default_device():
    ''' Connects to default android device (either emulator or physical phone) and returns monkeyrunner device'''

    default_logger = logging.getLogger('default')
    default_logger.info('Connecting to device...')

    # Connects to the current device, returning a MonkeyDevice object
    # the first argument is a timeout in seconds
    # the second argument is a regular expression describing the device ID (all can be found with "adb devices" command)
    # d = MonkeyRunner.waitForConnection(10, 'emulator-\d+') # connect to emulator
    device = MonkeyRunner.waitForConnection(10) # connect to default device
    default_logger.info('Connected to device!!')

    return device

def get_default_device_manager():
    ''' Connects to default android device and returns DeviceManager'''

    device = get_default_device()
    manager = DeviceManager(device)
    manager.log_info()

    return manager
