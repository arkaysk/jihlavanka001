"""Relácie, do ktorých sa dá prihlásiť: wayland-sessions a vo vývoji textová konzola."""
import configparser
import glob
import os
import shlex
from dataclasses import dataclass

from latte_common import build

SESSIONS_DIR = "/usr/share/wayland-sessions"
DEFAULT_SESSION_FILE = "latteos.desktop"


@dataclass
class Session:
    name: str
    cmd: list


is_dev = build.is_dev


def load(directory=SESSIONS_DIR, dev=None):
    """LatteOS prvý; potom ostatné relácie; vo vývoji aj konzola."""
    sessions = []
    for path in sorted(glob.glob(os.path.join(directory, "*.desktop"))):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read(path, encoding="utf-8")
            entry = parser["Desktop Entry"]
            name, exec_line = entry["Name"], entry["Exec"]
            if entry.getboolean("Hidden", False) or entry.getboolean("NoDisplay", False):
                continue
            cmd = shlex.split(exec_line)
        except (configparser.Error, KeyError, ValueError, OSError):
            continue
        if cmd:
            session = Session(name, cmd)
            if os.path.basename(path) == DEFAULT_SESSION_FILE:
                sessions.insert(0, session)
            else:
                sessions.append(session)
    if not sessions:
        sessions.append(Session("LatteOS", ["latteos-session"]))
    if is_dev() if dev is None else dev:
        sessions.append(Session("Konzola (headless)", ["latteos-console"]))
    return sessions
