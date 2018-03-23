#!/usr/bin/env bash

BASEDIR=$(dirname "$0")
~/Library/Android/sdk/tools/bin/monkeyrunner $BASEDIR/test.py
