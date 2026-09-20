#!/bin/bash
# latte-devices: Správca zariadení (hardvér po skupinách, monitory). Pozri src/latte_devices/app.py.
DIR=$(dirname "$(readlink -f "$0")")
exec python3 "$DIR/../src/latte_devices/app.py" "$@"
