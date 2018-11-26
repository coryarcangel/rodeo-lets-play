# watson-hollywood

A deep-q-learning trained bot that plays *Kim Kardashian: Hollywood*.

## Environment

1. Python environment managed with [pipenv](https://docs.pipenv.org/).
2. A gpu-enabled OpenCV-included installation of [darknet](https://pjreddie.com/darknet/install/) is required.
3. Before installing python requirements you will need to install libtesseract (>=3.04) and libleptonica (>=1.71) via brew or apt-get for [tesserocr](https://github.com/sirfz/tesserocr) to work.

## Directory Structure

* `src/ai` - neural net code; template for some parts taken from [reinforcement-learning](https://github.com/dennybritz/reinforcement-learning/)
* `src/monkeyrunner` - code to control the connected android emulator / device
* `apks` - Android APK files for the game itself

## Testing the Program
1. ./bin/start_vysor.sh — Ensure Vysor is up and running and can see connected Android Phone
2. ./bin/start_device_server.sh — Setup Device Server to receive commands from Device Client and send to phone (via Monkeyrunner)
3. ./bin/start_phone_stream.py — Start stream of images from phone to vysor for Screen Cap
4. ./bin/start_ai.sh — Starts the actual loop that grabs image state from phone stream and runs actions from it
