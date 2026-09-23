#!/bin/bash
# latte-appearance: služba (serve) aj príkazy (apply, status, set, ...). Pozri src/latte_appearance/app.py.
DIR=$(dirname "$(readlink -f "$0")")
exec python3 "$DIR/../src/latte_appearance/app.py" "$@"
