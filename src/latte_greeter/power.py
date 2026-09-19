"""Napájacie voľby prihlasovacej obrazovky.

Vypnutie a reštart počítača povoľuje logind. Reštart greetd a prechod do
textového režimu (multi-user.target) povoľuje pravidlo polkit
data/polkit/50-latteos-greeter.rules, ktoré nainštaluje tools/install-greeter.sh.
"""
import json
import subprocess
from dataclasses import dataclass


@dataclass
class Action:
    id: str
    label: str
    hint: str
    icon: str
    argv: list
    group: str                  # "pc" alebo "latteos"


ACTIONS = [
    Action("poweroff", "Vypnúť počítač", "vypne virtuálny stroj", "system-shutdown-symbolic",
           ["systemctl", "poweroff"], "pc"),
    Action("reboot", "Reštartovať počítač", "reštartuje virtuálny stroj", "system-reboot-symbolic",
           ["systemctl", "reboot"], "pc"),
    Action("restart-latteos", "Reštartovať LatteOS", "znovu načíta prihlasovanie",
           "view-refresh-symbolic", ["systemctl", "restart", "greetd"], "latteos"),
    Action("to-console", "Ukončiť do konzoly", "textový režim servera (headless)",
           "utilities-terminal-symbolic", ["systemctl", "isolate", "multi-user.target"], "latteos"),
]

TIMEOUT = 20


def other_users():
    """Mená používateľov s otvorenou reláciou (varovanie pred vypnutím)."""
    try:
        out = subprocess.run(
            ["loginctl", "--json=short", "list-sessions"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout
        sessions = json.loads(out)
    except (OSError, subprocess.SubprocessError, ValueError):
        return []
    names = []
    for s in sessions:
        user = s.get("user")
        if s.get("class") == "user" and user and user != "greetd" and user not in names:
            names.append(user)
    return names


def run(action):
    """Vykoná akciu; vráti None pri úspechu, inak text chyby."""
    try:
        result = subprocess.run(action.argv, capture_output=True, text=True, timeout=TIMEOUT)
    except (OSError, subprocess.SubprocessError) as err:
        return str(err)
    if result.returncode != 0:
        return (result.stderr or result.stdout).strip() or "kód %d" % result.returncode
    return None
