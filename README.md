# watson-hollywood

A deep-q-learning trained bot that plays *Kim Kardashian: Hollywood*.

## Environment

1. Python environment managed with [pipenv](https://docs.pipenv.org/).
2. A gpu-enabled OpenCV-included installation of [darknet](https://pjreddie.com/darknet/install/) is required.
3. Before installing python requirements you will need to install libtesseract (>=3.04) and libleptonica (>=1.71) via brew or apt-get for [tesserocr](https://github.com/sirfz/tesserocr) to work.
4. Jython made pipenv tricky I think. I would try installing the requirements directly to the system from requirements.txt with pip3.
  Everything except for the monkeyrunner stuff should be running in python 3 now.

## Vysor Config
1. Name the device "vysorkim" in the window settings
2. Uncheck the "navigation bar" option in window settings.
3. You can alter video quality settings as needed.
4. Save.

Cuda Version 9.0.176
OpenCV Version 2.4.9.1 (from `dpkg -l | grep libopencv`)
Might need to start redis on computer start (in the redis docs)
Node.js v12.16.1
Tensorflow 1.9.0
Ubuntu 16.04 LTS 64-bit
Nvidia Driver Version 384.130
Intel® Core™ i3-7100 CPU @ 3.90GHz × 4
Quadro FX NVS 810/PCIe/SSE2

Follow these instructions to prevent "login keyring did not open" error message
on first chrome open: https://askubuntu.com/questions/867/how-can-i-stop-being-prompted-to-unlock-the-default-keyring-on-boot

We start the process hub on boot by using Ubuntu's built-in "startup applications"
panel and running the `bin/start_all_delay.sh` script.
gnome-terminal -e /home/cory/watson-hollywood/bin/start_all_delay.sh --geometry="180x60+0+0"

kim_current_app_monitor currently runs inside of the frontend client.
maybe that could be better separated but I think its fine.

## Directory Structure

* `src/ai` - neural net code; template for some parts taken from [reinforcement-learning](https://github.com/dennybritz/reinforcement-learning/)
* `src/monkeyrunner` - code to control the connected android emulator / device
* `apks` - Android APK files for the game itself

## Testing the Program
1. ./process-hub/index.js (Uncomment AI Controller Line in `KimProcessManager` to run AI)

### The Process Hub Runs the following programs
1. ./process-hub/run_vysor.js — Starts Vysor and opens phone window
2. ./bin/start_device_server.sh — Setup Device Server to receive commands from Device Client and send to phone (via Monkeyrunner)
3. ./bin/start_frontend_server.sh — Sets up local webserver to serve image files and state updates to web renderer
4. ./bin/start_phone_stream.sh — Start stream of images from phone to vysor for Screen Cap
4.1 Currently the phone stream script also opens a chrome window to the web renderer, but I plan to make that an independent process.
5. ./bin/start_ai.sh — Starts the actual loop that grabs image state from phone stream and runs actions from it
