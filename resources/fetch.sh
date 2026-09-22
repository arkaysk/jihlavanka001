#!/usr/bin/env bash
# Fetches shallow, read-only copies of the upstream projects listed in ROADMAP.md
# ("Prebraté komponenty namiesto písania od nuly") for local inspection and as
# fork starting points. Re-run any time to refresh to the latest upstream commit.
#
# These clones are NOT tracked in git (see .gitignore: resources/*/) — only this
# script and MANIFEST.md are. That keeps the LatteOS repo small; the manifest
# pins the exact commit each clone was last refreshed at.
set -euo pipefail

cd "$(dirname "$0")"

clone() {
    local name="$1" url="$2" ref="${3:-}"
    if [ -d "$name/.git" ]; then
        echo "== $name: already present, skipping (delete dir to re-fetch) =="
        return
    fi
    echo "== $name =="
    if [ -n "$ref" ]; then
        git clone --depth 1 --branch "$ref" "$url" "$name"
    else
        git clone --depth 1 "$url" "$name"
    fi
    git -C "$name" rev-parse HEAD
}

# Etapa C — kompozitor (fork point, nie len referencia)
clone hyprland        https://github.com/hyprwm/Hyprland.git

# Etapa U — panel / launcher / kontextové menu / notifikácie
clone hyprpanel        https://github.com/Jas-SinghFSU/HyprPanel.git
clone quickshell        https://github.com/quickshell-mirror/quickshell.git
clone nwg-shell        https://github.com/nwg-piotr/nwg-shell.git

# Etapa D — súborový manažér
clone cosmic-files     https://github.com/pop-os/cosmic-files.git
clone cosmic-panel     https://github.com/pop-os/cosmic-panel.git
clone libcosmic        https://github.com/pop-os/libcosmic.git

# Etapa G — gaming session, Proton
clone gamescope        https://github.com/ValveSoftware/gamescope.git
clone umu-launcher     https://github.com/Open-Wine-Components/umu-launcher.git

# Etapa 0 / 9 — build/image pipeline referencia
clone bazzite          https://github.com/ublue-os/bazzite.git

echo "Hotovo. Pozri MANIFEST.md pre licencie a účel jednotlivých projektov."
