#!/bin/bash

set -e

python wimblepong.py "$@" &> log/game.log &
echo $! >> .pids
