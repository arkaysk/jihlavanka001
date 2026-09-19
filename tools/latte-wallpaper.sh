#!/bin/bash
# Nastaví tapetu plochy: latte-wallpaper set SÚBOR [cover|contain|fill] | reset | show.
# Dočasná náhrada za Nastavenia systému (etapa 8); píše ~/.config/latteos/appearance.toml.
DIR=$(dirname "$(readlink -f "$0")")
PYTHONPATH="$DIR/../src" exec python3 -m latte_common.wallpaper "$@"
