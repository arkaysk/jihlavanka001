#!/bin/sh
# Nainštaluje reláciu LatteOS pre aktuálneho používateľa. Symlinky, nie
# kópie, takže úpravy v repozitári platia hneď (po `systemctl --user daemon-reload`).
set -e
ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")
UNITS=$HOME/.config/systemd/user
BIN=$HOME/.local/bin

mkdir -p "$UNITS" "$BIN"
for unit in "$ROOT"/session/systemd/user/*; do
    ln -sf "$unit" "$UNITS/"
done
ln -sf "$ROOT/tools/run-shell.sh" "$BIN/latte-shell"
ln -sf "$ROOT/session/latteos-session" "$BIN/latteos-session"
[ -e "$HOME/.config/labwc" ] || ln -s "$ROOT/session/labwc" "$HOME/.config/labwc"
systemctl --user daemon-reload

echo "Hotovo. Reláciu spustíš z konzoly príkazom: latteos-session"
echo "Vývoj lišty: systemctl --user restart latte-shell"
echo "Výber relácie v prihlasovacom manažéri vyžaduje root:"
echo "  sudo install -m755 $ROOT/session/latteos-session /usr/local/bin/"
echo "  sudo install -m644 $ROOT/session/latteos.desktop /usr/share/wayland-sessions/"
