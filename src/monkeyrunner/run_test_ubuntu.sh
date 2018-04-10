#!/usr/bin/env bash

BASEDIR=$(dirname "$0")
~/Android/Sdk/tools/bin/monkeyrunner $BASEDIR/test.py
