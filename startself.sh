#!/bin/bash

set -e

python wimblepong.py wimble1 wimble2 "$@" &> log/game.log &
echo $! >> .pids

python wimblepong.py wimble2 wimble1 "$@" &
echo $! >> .pids
