#!/bin/sh
# Nainštaluje správcovského pomocníka správcu súborov (bod 1.10). Spúšťa sa ako root:
#   su -c 'sh tools/install-admin.sh'
# Pomocník beží ako root, preto sa KOPÍRUJE (nie symlink) do adresára, kam bežný
# používateľ nezapisuje. Po zmene kódu v repozitári treba skript spustiť znova.
set -e
[ "$(id -u)" = 0 ] || { echo "Spusti ako root." >&2; exit 1; }
ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")
LIB=/usr/libexec/latteos

install -d -m755 -o root -g root "$LIB"
install -m755 -o root -g root "$ROOT/src/latte_files/latte-files-admin" "$LIB/latte-files-admin"
install -m644 -o root -g root "$ROOT/src/latte_common/fileops.py" "$LIB/fileops.py"
install -m644 -o root -g root "$ROOT/data/polkit/org.latteos.files.admin.policy" \
    /usr/share/polkit-1/actions/org.latteos.files.admin.policy
restorecon -RF "$LIB" /usr/share/polkit-1/actions/org.latteos.files.admin.policy 2>/dev/null || true

echo "Nainštalované: $LIB a polkit politika org.latteos.files.admin."
