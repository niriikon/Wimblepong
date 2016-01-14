#!/bin/bash

set -e

python wimblepong.py wimblepong "$@" &> log/game.log &
echo $! >> .pids
