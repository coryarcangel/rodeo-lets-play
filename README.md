# watson-hollywood

A deep-q-learning trained bot that plays *Kim Kardashian: Hollywood*.

ab32902641a8a08aa6392eb715c655abf0d0b2c2

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

## Monitor Config
* Update the `MONITORS` variable in config.py with a list of up to 3 monitor names and their sizes (get names from xrandr)

## Tensorflow Agents Deep Q Config
* `TF_DEEPQ_POLICY_SAVE_DIR` in config.py is the location of the saved policy to load
* `TF_AI_POLICY_WEIGHTS` in config.py sets the probabilistic weights of each policy
in the `TfAgentBlendedPolicy` used in `tf_ai_runner` / process hub. These weights
should sum to 1.0. Set any of them to `0` to remove that policy (can do all random
or heuristic for testing, etc)

## Installing Python 3.8 / Conda for TF Agents
* sudo apt update -y
* sudo apt install python3.8
* download miniconda python 3.8 installer https://docs.conda.io/en/latest/miniconda.html#linux-installers
* Install with `bash ~/Downloads/Miniconda3-latest-Linux-x86_64.sh`. Select yes for last step of conda init.
* Docs here: https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html
* Run `conda config --set auto_activate_base false`
* Create environment with `conda create --name tf-ai-env python=3.8`
* Run `conda activate tf-ai-env` to activate environment
* Run `pip install -r tf_ai_env_pip_requirements.txt`

## Various Software Versions

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

`kim_current_app_monitor` currently runs inside of the frontend client.
maybe that could be better separated but I think its fine.

## Directory Structure

* `bin` - simple bash scripts to run the independent programs, used mainly in process hub
* `src` - all python code (tensorflow, vysor control, monkeyrunner, etc)
* `apks` - Android APK files for the game itself
* `process-hub` - Node.js program to coordinate all of the moving parts and monitor crashes, etc
* `logs` - Files written by process hub for each process
* `frontend-static` - Web javascript for rendering the frontend

## Testing the Program
1. ./process-hub/index.js
2. Thereis a command line option for `--startAll false` to not run the ai controller.

### The Process Hub Runs the following programs
1. ./process-hub/run_vysor.js — Starts Vysor and opens phone window
2. ./bin/start_device_server.sh — Setup Device Server to receive commands from Device Client and send to phone (via Monkeyrunner)
3. ./bin/start_frontend_server.sh — Sets up local webserver to serve image files and state updates to web renderer
4. ./bin/start_frontend_client.sh — Opens chrome window to web renderer, and runs
process to communicate with device server and ensure app stays as KK:Hollywood.
5. ./bin/start_phone_stream.sh — Start stream of images from phone to vysor for Screen Cap
6. ./bin/start_tf_ai.sh — Starts the actual loop that grabs image state from phone stream and runs actions from it
