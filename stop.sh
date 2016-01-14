#!/bin/bash

[ -r .pids ] || exit 0

while read line; do
    kill -9 $line &> /dev/null
done < .pids
rm .pids
