#!/bin/bash

set -e

mkdir -p log

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi
