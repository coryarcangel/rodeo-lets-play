#!/usr/bin/env bash

# This is meant to be run on computer startup.
# It will start the process hub after a small delay
# (to prevent race conditions I guess)

# Example command for startup running:
# gnome-terminal -e /home/cory/watson-hollywood/bin/start_all_delay.sh --geometry="180x60+0+0"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DELAY=${1:-30} # delay default to 30 seconds
startAll=${2:-true} # start all default to true

echo "waiting for $DELAY seconds before starting process hub..."
sleep $DELAY

# Have to run bash interactively for conda to work correctly.
# https://stackoverflow.com/questions/55507519/python-activate-conda-env-through-shell-script
echo "starting process hub"
cd $DIR/..
bash -i $DIR/start_all.sh
