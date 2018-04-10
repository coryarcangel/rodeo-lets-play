from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from random import randint

### Constants
DefaultCommunicationIP = '127.0.0.1'
DefaultCommunicationPort = 5005

BrowserPackage = 'com.android.chrome'
BrowserComponent = '%s/com.google.android.apps.chrome.Main' % BrowserPackage

KKHollywoodPackage = 'com.glu.stardomkim'
KKHollywoodComponent = '%s/com.google.android.vending.expansion.downloader_impl.DownloaderActivity' % KKHollywoodPackage

'''
Wrapper around MonkeyDevice with some higher-level controls.
'''
class DeviceManager:
    def __init__(self, device):
        self.device = device
        self.frame_count = 0

    def log_info(self):
        print('device name: %s' % self.device.getProperty('build.product'))
        print('device size: %sx%s' % (self.device.getProperty('display.width'), self.device.getProperty('display.height')))

    # component must be in the form: `PACKAGE_NAME/MAIN_ACTIVITY_NAME`
    def launch_app(self, component):
        categories = ['android.intent.category.LAUNCHER']
        self.device.startActivity(component=component, categories=categories)

    def restart_app(self, package, component):
        # simulate home press to return to menu
        self.device.press('KEYCODE_HOME', MonkeyDevice.DOWN_AND_UP)

        # kill the package
        self.device.shell('am force-stop %s' % package)

        # launch the app
        self.launch_app(component)

    def launch_browser(self):
        self.launch_app(BrowserComponent)

    def restart_browser(self):
        self.restart_app(BrowserPackage, BrowserComponent)

    def launch_hollywood(self):
        self.launch_app(KKHollywoodComponent)

    def restart_hollywood(self):
        self.restart_app(KKHollywoodPackage, KKHollywoodComponent)

    def get_screenshot(self):
        # get filename, increment frame count 
        filename = 'current_screen_%s.png' % self.frame_count
        self.frame_count += 1

        # acquire and save image
        img = self.device.takeSnapshot()
        img.writeToFile(filename)

        return filename

class DeviceMessageReceiver:
    def __init__(self, device_manager, ip = DefaultCommunicationIP, port = DefaultCommunicationPort):
        self.device_manager = device_manager

def get_default_device():
    ''' Connects to default android device (either emulator or physical phone) and returns monkeyrunner device'''
    
    print('Connecting to device...')
    # Connects to the current device, returning a MonkeyDevice object
    # the first argument is a timeout in seconds
    # the second argument is a regular expression describing the device ID (all can be found with "adb devices" command) - it can be left blank
    # d = MonkeyRunner.waitForConnection(10, 'emulator-\d+') # connect to emulator
    d = MonkeyRunner.waitForConnection(10) # connect to default device
    print('Connected!')
    
    return d

def get_default_device_manager():
    ''' Connects to default android device and returns DeviceManager'''

    d = get_default_device()
    dm = DeviceManager(d)
    dm.log_info()

    return dm