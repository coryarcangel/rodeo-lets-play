#!/usr/bin/env bash

# Set the SDK Path
SDK_PATH=~/Android/Sdk # Ubuntu
# SDK_PATH=~/Library/Android/sdk # OSX

# Get the directory where this script lives
BASEDIR=$(dirname "$0")

# Run the test
$SDK_PATH/tools/bin/monkeyrunner $BASEDIR/../src/test.py
