#!/bin/bash
# Polkit agent LatteOS. Spúšťa ho session/labwc/autostart (musí byť potomok labwc,
# nie user služba; dôvod je tam). Po páde ho reštartuje; ak zlyháva hneď po štarte
# (napr. už beží iný agent), po piatich pokusoch to vzdá a povie prečo.
DIR=$(dirname "$(readlink -f "$0")")
fails=0
while true; do
    started=$(date +%s)
    python3 "$DIR/../src/latte_polkit/agent.py"
    rc=$?
    [ "$rc" -eq 0 ] && exit 0
    if [ $(( $(date +%s) - started )) -lt 5 ]; then fails=$((fails + 1)); else fails=0; fi
    if [ "$fails" -ge 5 ]; then
        echo "latte-polkit: agent opakovane zlyháva hneď po štarte (kód $rc), vzdávam to" >&2
        exit 1
    fi
    sleep 1
done
