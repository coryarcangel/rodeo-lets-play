from com.android.monkeyrunner import MonkeyDevice

### Constants
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