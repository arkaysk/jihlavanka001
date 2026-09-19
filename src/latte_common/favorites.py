"""Obľúbené priečinky (bod 1.12): ~/.config/latteos/favorites.toml."""
import json
import os
import sys
import tomllib

from latte_common.volumes import CONFIG_DIR


def _file():
    return os.path.join(CONFIG_DIR, "favorites.toml")


def load():
    try:
        with open(_file(), "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return []
    except (OSError, tomllib.TOMLDecodeError) as err:
        print("latte-favorites: %s sa nedá prečítať: %s" % (_file(), err), file=sys.stderr)
        return []
    paths = []
    for item in data.get("favorite", []):
        path = item.get("path") if isinstance(item, dict) else None
        if isinstance(path, str) and path.startswith("/") and path not in paths:
            paths.append(path)
    return paths


def save(paths):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    lines = ["# Obľúbené priečinky LatteOS", ""]
    for path in paths:
        lines += ["[[favorite]]", "path = " + json.dumps(path, ensure_ascii=False), ""]
    tmp = _file() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    os.replace(tmp, _file())


def add(path):
    paths = load()
    if path not in paths:
        paths.append(path)
        save(paths)
    return paths


def remove(path):
    paths = [p for p in load() if p != path]
    save(paths)
    return paths
