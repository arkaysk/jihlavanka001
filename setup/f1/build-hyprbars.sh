#!/usr/bin/env bash
# Postaví plugin hyprbars (okenné tlačidlá LatteOS, latte/bars.lua) proti nainštalovanému hyprland-devel.
# Commit hyprland-plugins sa berie z hyprpm.toml podľa verzie Hyprlandu (napr. 0.56.2 → 7644cec…).
set -euo pipefail
repo="$(cd "$(dirname "$0")/../.." && pwd)"
src="$repo/resources/upstream/hyprland-plugins"
[ -d "$src/.git" ] || git clone -q https://github.com/hyprwm/hyprland-plugins.git "$src"
ver="$(pkg-config --modversion hyprland)"
commit="$(grep -F "# $ver" "$src/hyprpm.toml" | head -1 | sed -E 's/.*", "([0-9a-f]+)".*/\1/')"
[ -n "$commit" ] || { echo "hyprpm.toml nepozná Hyprland $ver"; exit 1; }
git -C "$src" fetch -q origin 2>/dev/null || true
git -C "$src" checkout -q "$commit"
make -C "$src/hyprbars" -j"$(nproc)" >/dev/null
echo "$src/hyprbars/hyprbars.so (Hyprland $ver, hyprland-plugins $commit)"
