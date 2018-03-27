# watson-hollywood

A deep-q-learning trained bot that plays *Kim Kardashian: Hollywood*.

## Environment

1. Python environment managed with [pipenv](https://docs.pipenv.org/).
2. A gpu-enabled OpenCV-included installation of [darknet](https://pjreddie.com/darknet/install/) is required.

## Directory Structure

* `src/ai` - neural net code; template for some parts taken from [reinforcement-learning](https://github.com/dennybritz/reinforcement-learning/)
* `src/monkeyrunner` - code to control the connected android emulator / device
* `apks` - Android APK files for the game itself
