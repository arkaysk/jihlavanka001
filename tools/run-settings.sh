#!/bin/bash
# latte-settings: Nastavenia systému. Voliteľný odkaz: latte-settings settings://environment/theme
# (oblasť/stránka, oblasť alebo id stránky). Pozri src/latte_settings/app.py.
DIR=$(dirname "$(readlink -f "$0")")
exec env GSK_RENDERER=cairo python3 "$DIR/../src/latte_settings/app.py" "$@"
