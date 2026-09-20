#!/bin/bash
# Proces Manažér/Monitor LatteOS.
DIR=$(dirname "$(readlink -f "$0")")
exec env GSK_RENDERER=cairo python3 "$DIR/../src/latte_process/app.py" "$@"
