"""Malé nastavenia komponentov: ~/.config/latteos/<komponent>.toml (len reťazce).

Čítanie cez tomllib; pri poškodenom súbore sa použijú predvolené hodnoty a chyba ide na stderr.
"""
import json
import os
import sys
import tomllib

from latte_common.volumes import CONFIG_DIR


def _file(component):
    return os.path.join(CONFIG_DIR, component + ".toml")


def load(component):
    try:
        with open(_file(component), "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, tomllib.TOMLDecodeError) as err:
        print("latte-prefs: %s sa nedá prečítať: %s" % (_file(component), err), file=sys.stderr)
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str)}


def save(component, values):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    lines = ["# Nastavenia komponentu %s" % component]
    lines += ["%s = %s" % (key, json.dumps(str(value), ensure_ascii=False)) for key, value in sorted(values.items())]
    tmp = _file(component) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(tmp, _file(component))


def update(component, **changes):
    """Zmení len uvedené kľúče, ostatné ponechá."""
    values = load(component)
    values.update({k: str(v) for k, v in changes.items()})
    save(component, values)
    return values
