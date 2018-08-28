#!/usr/bin/env bash

# Set the SDK Path
 SDK_PATH=~/Android/Sdk # Ubuntu
#SDK_PATH=~/Library/Android/sdk # OSX

# Get the directory where this script lives
BASEDIR=$(dirname "$0")

# Run the appropriate script based on command
COMMAND=$1
case "$COMMAND" in
"test")
    # Run monkeyrunner test
    $SDK_PATH/tools/bin/monkeyrunner $BASEDIR/../src/monkey_test.py
    ;;
"device_server")
    $SDK_PATH/tools/bin/monkeyrunner $BASEDIR/../src/device_server.py
    ;;
*)
    echo "command \"$COMMAND\" not recognized..."
    ;;
esac
