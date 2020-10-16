#!/usr/bin/env bash

# This is meant to be run on computer startup.
# It will start the process hub after a small delay
# (to prevent race conditions I guess)

# Example command for startup running:
# gnome-terminal -e /home/cory/watson-hollywood/bin/start_all_delay.sh --geometry="180x60+0+0"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DELAY=${1:-30} # delay default to 30 seconds

echo "waiting for $DELAY seconds before starting process hub..."
sleep $DELAY

echo "starting process hub"
cd $DIR/..
node process-hub/index.js
