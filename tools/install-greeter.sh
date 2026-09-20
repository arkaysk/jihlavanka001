#!/bin/sh
# Nainštaluje prihlasovaciu obrazovku LatteOS (greetd + latte-greeter). Spúšťa sa ako root:
#   su -c 'sh tools/install-greeter.sh'
# Predpoklad: dnf install greetd gtkgreet (a greetd-selinux pri zapnutom SELinuxe).
# gtkgreet ostáva ako záloha, ak by latte-greeter spadol.
# Greeter beží ako používateľ greetd a domovské adresáre nevidí, preto sa jeho kód a
# dáta KOPÍRUJÚ (nie symlink) do /usr/local. Po zmene kódu spusti skript znova.
# Zapnutie greeteru (systemctl enable greetd) nerobí, vypíše ho na konci.
set -e
[ "$(id -u)" = 0 ] || { echo "Spusti ako root." >&2; exit 1; }
ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")
LIB=/usr/local/lib/latteos
SHARE=/usr/local/share/latteos

# príkazy relácie a diagnostiky
for cmd in latteos-session latteos-console latteos-diag latteos-start latteos-logout latte-greeter; do
    install -m755 "$ROOT/session/$cmd" "/usr/local/bin/$cmd"
done
install -m644 "$ROOT/session/latteos.desktop" /usr/share/wayland-sessions/latteos.desktop

# kód greetera (Python) a spoločné moduly
rm -rf "$LIB/latte_common" "$LIB/latte_greeter"
install -d -m755 "$LIB/latte_common" "$LIB/latte_greeter"
for f in "$ROOT"/src/latte_common/*.py; do install -m644 "$f" "$LIB/latte_common/"; done
for f in "$ROOT"/src/latte_greeter/*.py; do install -m644 "$f" "$LIB/latte_greeter/"; done
chmod 755 "$LIB/latte_greeter/app.py"

# téma (štýly, motívy, schémy nastavení, ktoré latte_common/theme.py potrebuje) a systémové tapety
rm -rf "$SHARE/styles" "$SHARE/wallpapers" "$SHARE/themes" "$SHARE/settings"
install -d -m755 "$SHARE/styles" "$SHARE/wallpapers" "$SHARE/themes" "$SHARE/settings"
install -m644 "$ROOT"/data/styles/latte.css "$SHARE/styles/"
for f in "$ROOT"/data/wallpapers/*; do install -m644 "$f" "$SHARE/wallpapers/"; done
for d in "$ROOT"/data/themes/*/; do install -d -m755 "$SHARE/themes/$(basename "$d")"; install -m644 "$d"* "$SHARE/themes/$(basename "$d")/"; done
install -m644 "$ROOT"/data/settings/*.toml "$SHARE/settings/"

# záznamy o skončení relácií: každý používateľ smie prepísať len svoj súbor (sticky bit)
install -d -m755 /var/lib/latteos
install -d -m1777 /var/lib/latteos/last-exit

# napájacie voľby greetera
install -m644 "$ROOT/data/polkit/50-latteos-greeter.rules" /etc/polkit-1/rules.d/50-latteos-greeter.rules
# Iba dev build: "Vypnúť" v systémovom manažéri prepne do konzoly bez hesla.
# Pre vydanie tento súbor neinštalovať (ak /etc/latteos/release existuje, preskočí sa).
if [ -e /etc/latteos/release ]; then
    rm -f /etc/polkit-1/rules.d/51-latteos-dev.rules
else
    install -m644 "$ROOT/data/polkit/51-latteos-dev.rules" /etc/polkit-1/rules.d/51-latteos-dev.rules
fi

[ -e /etc/greetd/config.toml.orig ] || cp /etc/greetd/config.toml /etc/greetd/config.toml.orig
install -m644 "$ROOT/session/greetd/config.toml" /etc/greetd/config.toml

# Zoznam relácií pre záložný gtkgreet sa skladá z wayland-sessions (pomocník od Fedory).
/usr/libexec/gtkgreet-update-environments --write
# Vývoj: vstup do konzoly (nie je Wayland relácia, preto nie je v wayland-sessions).
echo latteos-console >> /etc/greetd/environments

restorecon -RF /usr/local/bin/latteos-* /usr/local/bin/latte-greeter "$LIB" "$SHARE" \
    /var/lib/latteos /usr/share/wayland-sessions/latteos.desktop \
    /etc/greetd/config.toml /etc/greetd/environments \
    /etc/polkit-1/rules.d/50-latteos-greeter.rules /etc/polkit-1/rules.d/51-latteos-dev.rules 2>/dev/null || true

echo "Nainštalované. Zapnutie prihlasovacej obrazovky:"
echo "  systemctl set-default graphical.target && systemctl enable greetd"
echo "Použije sa pri ďalšom štarte greetd (systemctl restart greetd ukončí aktuálne prihlásenie)."
echo "Ak sa greeter nespustí, skontroluj SELinux: ausearch -m avc -ts recent"
echo "Vrátenie: systemctl disable greetd && systemctl set-default multi-user.target"
