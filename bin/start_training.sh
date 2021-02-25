#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

NODE_ENV=PRODUCTION node $DIR/../process-hub/index.js --startAll t --train t
