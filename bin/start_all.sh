#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
startAll=${1:-true} # start all default to true

node $DIR/../process-hub/index.js --startAll $startAll
