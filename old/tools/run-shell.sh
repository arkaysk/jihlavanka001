#!/bin/bash
# Spustí lištu LatteOS. LD_PRELOAD je nutný, aby gtk4-layer-shell
# bola v pamäti skôr než libwayland-client.
LIB=$(ls /usr/lib64/libgtk4-layer-shell.so* 2>/dev/null | head -n1)
DIR=$(dirname "$(readlink -f "$0")")
exec env LD_PRELOAD="$LIB" GSK_RENDERER=cairo python3 "$DIR/../src/latte_shell/app.py"