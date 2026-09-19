#!/bin/sh
# Nainštaluje prihlasovaciu obrazovku LatteOS (greetd + gtkgreet). Spúšťa sa ako root:
#   su -c 'sh tools/install-greeter.sh'
# Predpoklad: dnf install greetd gtkgreet (a greetd-selinux pri zapnutom SELinuxe).
# Zapnutie greeteru (systemctl enable greetd) nerobí, vypíše ho na konci.
set -e
ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")

install -m755 "$ROOT/session/latteos-session" /usr/local/bin/latteos-session
install -m755 "$ROOT/session/latteos-console" /usr/local/bin/latteos-console
install -m644 "$ROOT/session/latteos.desktop" /usr/share/wayland-sessions/latteos.desktop

[ -e /etc/greetd/config.toml.orig ] || cp /etc/greetd/config.toml /etc/greetd/config.toml.orig
install -m644 "$ROOT/session/greetd/config.toml" /etc/greetd/config.toml

# Zoznam relácií pre gtkgreet sa skladá z wayland-sessions (pomocník od Fedory).
/usr/libexec/gtkgreet-update-environments --write
# Vývoj: vstup do konzoly (nie je Wayland relácia, preto nie je v wayland-sessions).
echo latteos-console >> /etc/greetd/environments

restorecon -F /usr/local/bin/latteos-session /usr/local/bin/latteos-console \
    /usr/share/wayland-sessions/latteos.desktop \
    /etc/greetd/config.toml /etc/greetd/environments

echo "Nainštalované. Zapnutie prihlasovacej obrazovky:"
echo "  systemctl set-default graphical.target && systemctl enable greetd"
echo "Vrátenie: systemctl disable greetd && systemctl set-default multi-user.target"
