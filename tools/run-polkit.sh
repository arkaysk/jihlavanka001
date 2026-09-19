#!/bin/bash
# Spustí polkit agenta LatteOS (latte-polkit.service).
DIR=$(dirname "$(readlink -f "$0")")
exec python3 "$DIR/../src/latte_polkit/agent.py"
