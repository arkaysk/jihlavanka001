#!/usr/bin/env bash
# F1 — nainštaluje štart LatteOS do systému: latte-boot, relácie NORMAL/SAFE, greeter, GRUB SAFE, Plymouth.
# Spúšťať ako bežný používateľ (build ide bez roota, inštalácia cez sudo):
#   setup/f1/install-session.sh            nainštaluje a pripraví, grafický štart NEZAPNE
#   setup/f1/install-session.sh --enable   navyše zapne latte-boot + greetd a graphical.target
# Opätovné spustenie je bezpečné (prepíše súbory LatteOS, pôvodné konfigurácie zálohuje raz).
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
S="$repo/session"
enable=0; [ "${1:-}" = --enable ] && enable=1
[ "$(id -u)" -ne 0 ] || { echo "Spúšťaj ako používateľ (nie cez sudo); skript si sudo vyžiada sám."; exit 1; }
user="$(id -un)"
# bez terminálu (automatizácia): SUDO_ASKPASS=<skript> → sudo -A
sudo() { if [ -n "${SUDO_ASKPASS:-}" ]; then command sudo -A "$@"; else command sudo "$@"; fi; }

echo "== build latte-boot"
(cd "$repo" && cargo build --release --offline -q)

echo "== skupina latte (zápis počítadla pádov z relácie)"
sudo groupadd -f latte
sudo usermod -aG latte "$user"

echo "== binárky a skripty → /usr/bin"
sudo install -Dm755 "$repo/target/release/latte-boot" /usr/bin/latte-boot
for f in latte-session latte-safe latte-greeter latte-theme latte-app; do sudo install -Dm755 "$S/bin/$f" "/usr/bin/$f"; done

echo "== konfigurácie relácií → /usr/share/latteos"
sudo install -Dm644 "$S/hypr/hyprland.conf" /usr/share/latteos/hypr/hyprland.conf
sudo install -Dm644 "$S/hypr/hyprland.lua" /usr/share/latteos/hypr/hyprland.lua
sudo install -d /usr/share/latteos/hypr/latte
sudo install -m644 "$S"/hypr/latte/*.lua /usr/share/latteos/hypr/latte/
for f in rc.xml autostart environment menu.xml; do sudo install -Dm644 "$S/labwc/$f" "/usr/share/latteos/labwc/$f"; done
# relácie LatteOS: v systémovom zozname (pre iné greetery) aj vo vlastnom, ktorý ponúka latte-greeter
# (tuigreet by inak ponúkol aj „Hyprland“ z COPR bez Noctalie a bez latte-session)
for f in latteos.desktop latteos-safe.desktop; do
    sudo install -Dm644 "$S/wayland-sessions/$f" "/usr/share/wayland-sessions/$f"
    sudo install -Dm644 "$S/wayland-sessions/$f" "/usr/share/latteos/sessions/$f"
done

echo "== vzhľad: Noctalia (téma Latte), písma Manrope/Fraunces (OFL), tapety LatteOS"
sudo install -Dm644 "$S/noctalia/config.toml" /usr/share/latteos/noctalia/config.toml
sudo install -Dm644 "$S/noctalia/palettes/Latte.json" /usr/share/latteos/noctalia/palettes/Latte.json
sudo install -Dm644 "$S/noctalia/icons/latte-cup.png" /usr/share/latteos/noctalia/icons/latte-cup.png
for p in "$S"/noctalia/plugins/*/; do   # pluginy LatteOS (zdroj „latteos“ v config.toml)
    n="$(basename "$p")"; sudo install -d "/usr/share/latteos/noctalia/plugins/$n"
    sudo install -m644 "$p"* "/usr/share/latteos/noctalia/plugins/$n/"
done
sudo install -d /usr/share/fonts/latteos /usr/share/backgrounds/latteos
sudo install -m644 "$S"/fonts/*.ttf "$S"/fonts/OFL-*.txt /usr/share/fonts/latteos/
sudo fc-cache -f /usr/share/fonts/latteos
sudo install -m644 "$S"/wallpapers/*.jpg /usr/share/backgrounds/latteos/
sudo install -d /usr/share/latteos/themes
sudo install -m644 "$S"/themes/*.theme /usr/share/latteos/themes/
sudo install -m644 "$S"/noctalia/palettes/*.json /usr/share/latteos/noctalia/palettes/

echo "== greeter LatteOS (Quickshell QML pod labwc + pixman)"
sudo install -Dm644 "$S/greeter/shell.qml" /usr/share/latteos/greeter/shell.qml
for f in rc.xml environment; do sudo install -Dm644 "$S/greeter/labwc/$f" "/usr/share/latteos/greeter/labwc/$f"; done

echo "== aplikácie LatteOS (Quickshell QML): Súbory"
sudo install -d /usr/share/latteos/apps/common /usr/share/latteos/apps/data
sudo install -m644 "$S"/apps/*.qml /usr/share/latteos/apps/
sudo install -m644 "$S"/apps/common/*.qml /usr/share/latteos/apps/common/
sudo install -m644 "$S"/apps/data/*.qml /usr/share/latteos/apps/data/
sudo install -m644 "$S"/apps/*.desktop /usr/share/applications/
xdg-mime default latteos-subory.desktop inode/directory 2>/dev/null || true

echo "== systemd + tmpfiles + /etc/latteos"
sudo install -Dm644 "$S/systemd/latte-boot.service" /usr/lib/systemd/system/latte-boot.service
sudo install -Dm644 "$S/systemd/latteos.tmpfiles" /usr/lib/tmpfiles.d/latteos.conf
# SELinux: greeter beží v doméne xdm_t a smie čítať iba xdm_var_run_t → štítok pre /run/latteos
# (bez neho greeter nevidí session.env a vždy ponúkne SAFE; zistené testom 23. 9. 2026)
if command -v semanage >/dev/null || sudo dnf -y -q install policycoreutils-python-utils; then
    sudo semanage fcontext -l | grep -q '^/run/latteos' || sudo semanage fcontext -a -t xdm_var_run_t '/run/latteos(/.*)?'
fi
sudo systemd-tmpfiles --create /usr/lib/tmpfiles.d/latteos.conf
sudo restorecon -R /run/latteos
[ -f /etc/latteos/boot.toml ] || sudo install -Dm644 "$S/etc/boot.toml" /etc/latteos/boot.toml
# nové kľúče doplniť do existujúceho boot.toml (hodnoty používateľa sa nemenia)
grep -q '^greeter' /etc/latteos/boot.toml || sed -n '/^# obrazovka prihlásenia/,/^greeter/p' "$S/etc/boot.toml" | sudo tee -a /etc/latteos/boot.toml >/dev/null
sudo systemctl daemon-reload

echo "== greetd → latte-greeter (záloha pôvodnej konfigurácie raz)"
[ -f /etc/greetd/config.toml.pre-latteos ] || sudo cp -a /etc/greetd/config.toml /etc/greetd/config.toml.pre-latteos
sudo install -Dm644 "$S/greetd/config.toml" /etc/greetd/config.toml

echo "== GRUB: položky LatteOS SAFE pre nainštalované kernely"
sudo install -Dm755 "$S/kernel-install/96-latteos-safe.install" /etc/kernel/install.d/96-latteos-safe.install
for k in /lib/modules/*/; do
    v="$(basename "$k")"
    [ -e "/boot/vmlinuz-$v" ] && sudo /etc/kernel/install.d/96-latteos-safe.install add "$v"
done
sudo sh -c 'ls /boot/loader/entries/' | sed 's/^/   /'

echo "== Plymouth téma latteos"
th=/usr/share/plymouth/themes/latteos
sudo install -d "$th"
sudo install -m644 "$S/plymouth/latteos/latteos.plymouth" "$th/latteos.plymouth"
# otáčadlo a ikonky dialógov (heslo, capslock…) zo systémovej témy spinner, potom naše logo navrch
sudo sh -c "cp -f /usr/share/plymouth/themes/spinner/*.png $th/"
tmp="$(mktemp --suffix=.png)"
python3 "$S/plymouth/latteos/make-logo.py" "$tmp" 192
sudo install -m644 "$tmp" "$th/watermark.png"
rm -f "$tmp"
if [ "$(plymouth-set-default-theme)" != latteos ]; then
    echo "   plymouth-set-default-theme latteos -R (prestavba initramfs, ~1 min)"
    sudo plymouth-set-default-theme latteos -R
fi

echo "== hyprland-latte: lokálny repozitár, COPR ho nesmie prepísať"
rpm -q createrepo_c >/dev/null || sudo dnf -y -q install createrepo_c
sudo install -d /var/lib/latteos/repo
sudo cp -f "$HOME"/rpmbuild/RPMS/x86_64/hyprland-{0,devel-0,uwsm-0}*.latte.*.rpm /var/lib/latteos/repo/ 2>/dev/null || true
sudo createrepo_c -q /var/lib/latteos/repo
sudo tee /etc/yum.repos.d/latteos-local.repo >/dev/null <<'REPO'
[latteos-local]
name=LatteOS lokálne balíky (hyprland-latte s vmwgfx patchom)
baseurl=file:///var/lib/latteos/repo
enabled=1
gpgcheck=0
priority=10
REPO
copr=/etc/yum.repos.d/_copr:copr.fedorainfracloud.org:lionheartp:Hyprland.repo
if [ -f "$copr" ] && ! grep -q '^excludepkgs=hyprland' "$copr"; then
    sudo sed -i '/^\[copr:copr.fedorainfracloud.org:lionheartp:Hyprland\]/a excludepkgs=hyprland,hyprland-devel,hyprland-uwsm,hyprland-debuginfo,hyprland-debugsource' "$copr"
fi

echo "== prvý výber režimu"
sudo systemctl restart latte-boot.service || sudo latte-boot select
latte-boot status | sed 's/^/   /'
{ Hyprland --verify-config -c /usr/share/latteos/hypr/hyprland.lua 2>&1 || true; } | tail -2 | sed 's/^/   Hyprland: /'

if [ $enable -eq 1 ]; then
    echo "== zapínam grafický štart: latte-boot + greetd, graphical.target"
    sudo systemctl enable latte-boot.service greetd.service
    sudo systemctl set-default graphical.target
    echo "   Pri ďalšom reštarte naštartuje LatteOS greeter. Konzola ostáva na Ctrl+Alt+F2, SSH beží ďalej."
else
    echo "== grafický štart NIE je zapnutý (spusti s --enable)"
fi
echo "Hotovo. Nová skupina latte platí po novom prihlásení používateľa $user."
